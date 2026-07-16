# -*- coding: utf-8 -*-
"""오픈형 상품1·2 장기 백테스트 — K200 / 삼성전자 / SK하이닉스
- 기간: 보유 데이터 전체 (xlsx 실거래일, 2021-07 ~ 2026-07-10, 약 5년) ※10년 데이터 확보 시 자동 확장
- 상품1 룰베이스(k=1.25) / 상품2 옵션모형(T=0.25 고정, K역산) / BM150 고정 / 기초 1배
- 분기(63영업일) 리셋, 거래비용 15bps, r=2.5%, 가격수익률
"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
from scipy.special import ndtr as N
from scipy.optimize import brentq
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#9DB4CC'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

RQ=0.025; TFIX=0.25; TC=0.0015; RESET=63; K_STD=1.25
def put_delta(S,K,sig):
    sq=sig*math.sqrt(TFIX); d1=(math.log(S/K)+(0.5*sig*sig)*TFIX)/sq
    return math.exp(-RQ*TFIX)*(N(d1)-1.0)
def calib_ratio(sig):
    return brentq(lambda x:(1.0-put_delta(100.0,100.0*x,sig))-1.5,0.7,1.4)

def series(sheet,colidx):
    raw=pd.read_excel(XLS,sheet_name=sheet,header=None); d=raw.iloc[14:]
    dt=pd.to_datetime(d.iloc[:,0]); px=pd.to_numeric(d.iloc[:,colidx],errors='coerce')
    s=pd.Series(px.values,index=dt.values).dropna()
    idx=pd.to_datetime(s.index); s=s[idx.dayofweek<5]
    chg=s.pct_change().fillna(1.0); return s[chg!=0]     # 실거래일만

def backtest(px,sig,label,tag):
    dts=pd.to_datetime(px.index); S=px.values.astype(float)
    ASOF=pd.Timestamp(dts[-1]).strftime('%Y-%m-%d'); START=pd.Timestamp(dts[0]).strftime('%Y-%m-%d')
    yrs=(dts[-1]-dts[0]).days/365.25
    kr=calib_ratio(sig); n=len(S); rday=RQ/252
    V={'p1':1.0,'p2':1.0,'bm':1.0}; navs={k:[1.0] for k in V}
    S0=S[0]; K=S0*kr
    w1=lambda s: min(max(1.5-K_STD*(s/S0-1.0),1.0),2.0)
    w2=lambda s: min(max(1.0-put_delta(s,K,sig),1.0),2.0)
    w={'p1':w1(S[0]),'p2':w2(S[0]),'bm':1.5}
    ww={'p1':[w['p1']],'p2':[w['p2']]}; resets=[]
    for t in range(1,n):
        r=S[t]/S[t-1]-1.0
        for k in V: V[k]*=1.0+w[k]*r+(1.0-w[k])*rday
        if t%RESET==0:
            S0=S[t]; K=S0*kr; resets.append(dts[t])
        nw={'p1':w1(S[t]),'p2':w2(S[t]),'bm':1.5}
        for k in ('p1','p2'): V[k]-=TC*abs(nw[k]-w[k])*V[k]
        w=nw
        for k in V: navs[k].append(V[k])
        ww['p1'].append(w['p1']); ww['p2'].append(w['p2'])
    res={k:np.asarray(v) for k,v in navs.items()}; base=S/S[0]
    def stats(nav):
        cagr=(nav[-1]**(1/yrs)-1)*100
        dr=np.diff(nav)/nav[:-1]; vol=dr.std()*math.sqrt(252)*100
        mdd=((nav/np.maximum.accumulate(nav))-1).min()*100
        return (nav[-1]-1)*100,cagr,vol,mdd
    print(f"\n===== {label} ({START} ~ {ASOF}, {yrs:.1f}년) · σ가정 {int(sig*100)}% · 상품2 K/S₀={kr*100:.1f}% =====")
    print(f"{'':14}{'누적수익':>10}{'연복리':>8}{'연변동성':>8}{'MDD':>8}")
    rows={}
    for nm,nav in (('기초 1배',base),('BM150 고정',res['bm']),('상품1 룰베이스',res['p1']),('상품2 옵션모형',res['p2'])):
        a,c,v,m=stats(np.asarray(nav)); rows[nm]=(a,c,v,m)
        print(f"{nm:14}{a:+9.0f}%{c:+7.1f}%{v:7.1f}%{m:+7.1f}%")
    # ---- 차트 ----
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(8.8,6.4),dpi=105,height_ratios=[1.7,1],sharex=True)
    ax1.plot(dts,base*100,color=SKY,lw=1.6,label='기초 1배')
    ax1.plot(dts,res['bm']*100,color=GRAY,lw=1.6,ls='--',label='BM 150% 고정')
    ax1.plot(dts,res['p1']*100,color=NAVY,lw=2.0,label='상품1 룰베이스(k=1.25)')
    ax1.plot(dts,res['p2']*100,color=ORANGE,lw=2.0,label='상품2 옵션모형(T=0.25)')
    ax1.set_yscale('log')
    yt=[50,100,200,400,800,1600,3200,6400]
    ymax=max(res['bm'].max(),res['p1'].max(),res['p2'].max(),base.max())*100
    yt=[v for v in yt if v<ymax*1.6]
    ax1.set_yticks(yt); ax1.set_yticklabels([str(v) for v in yt])
    ax1.axhline(100,color='#9db4cc',lw=0.8)
    for nav,col in ((res['p1'],NAVY),(res['p2'],ORANGE),(res['bm'],GRAY),(base,SKY)):
        v=np.asarray(nav)[-1]*100
        ax1.annotate(f'{v-100:+,.0f}%',xy=(dts[-1],v),xytext=(5,0),textcoords='offset points',color=col,fontsize=10.5,fontweight='bold',va='center')
    ax1.set_xlim(dts[0],dts[-1]+pd.Timedelta(days=45))
    ax1.set_ylabel('NAV (시작=100, 로그)',color=NAVY,fontsize=11)
    ax1.set_title(f'{label} — 오픈형 변동성 하베스트 장기 백테스트 ({yrs:.1f}년)',color=NAVY,fontsize=14,fontweight='bold',loc='left',pad=10)
    ax1.legend(fontsize=9.5,frameon=False,loc='upper left'); ax1.grid(alpha=0.2,which='both')
    ax1.spines[['top','right']].set_visible(False)
    ax2.plot(dts,np.asarray(ww['p1'])*100,color=NAVY,lw=1.1,label='상품1 편입비')
    ax2.plot(dts,np.asarray(ww['p2'])*100,color=ORANGE,lw=1.1,alpha=0.85,label='상품2 편입비')
    for y in (100,150,200): ax2.axhline(y,color='#e5e5e5',lw=0.8,ls='--' if y==150 else ':')
    ax2.set_ylim(90,210); ax2.set_ylabel('편입비 (%)',color=NAVY,fontsize=10.5)
    ax2.legend(fontsize=9,frameon=False,loc='upper left'); ax2.grid(alpha=0.2)
    ax2.spines[['top','right']].set_visible(False)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    fig.text(0.98,0.012,f'데이터 기준일: {ASOF} ({START}~{ASOF}, 실거래일) · σ가정 {int(sig*100)}% · 분기(63영업일) 리셋 · 비용 15bps · r=2.5% · 가격수익률(배당 미반영)',
             ha='right',color=GRAY,fontsize=7.6)
    fig.tight_layout(rect=[0,0.03,1,1])
    fig.savefig(os.path.join(IMG,f'open_bt5y_{tag}.png')); plt.close(fig)
    print(f"saved open_bt5y_{tag}.png")

backtest(series('코스피_코스피200_코스닥150',8),0.50,'KOSPI200','k200')
backtest(series('삼성전자_하이닉스',4),0.60,'삼성전자','samsung')
backtest(series('삼성전자_하이닉스',8),0.60,'SK하이닉스','hynix')
