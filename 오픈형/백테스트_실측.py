# -*- coding: utf-8 -*-
"""오픈형 변동성 하베스트 레버리지 — 실측 데이터 백테스트 (최종 설계안)
- 기초: KOSPI200 지수(σ가정 50%) / SK하이닉스 주가(σ가정 60%), 최근 1년 (데이터 ~2026-07-10)
- 상품1 룰베이스: w = 150% − 1.25×(S/S₀−1), 캡 [100,200]  (±40% 설계)
- 상품2 옵션복제: w = 100% + 풋매도 복제비중(행사가 K, 고정만기 T=0.25), K는 리셋 시 w=150% 역산
- 리셋: 63영업일(분기)마다 기준(S₀/K) 재설정 → 150% 복귀 (트랜치 스무딩은 미적용·단순화)
- 비용/가정: 거래비용 15bps, 자금조달·현금금리 r=2.5%(레버리지 차입비용), 가격수익률 기준(배당 미반영)
- 비교: 기초 1배, BM 150% 고정(일별 리밸런싱)
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
NAVY='#043B72'; ORANGE='#F58220'; RED='#C0392B'; GRAY='#84888B'; SKY='#9DB4CC'; GREEN='#1F9E6E'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

RQ=0.025; TFIX=0.25; TC=0.0015; RESET=63; K_STD=1.25
def put_delta(S,K,sig):
    sq=sig*math.sqrt(TFIX); d1=(math.log(S/K)+(0.5*sig*sig)*TFIX)/sq   # r=q → r-q=0
    return math.exp(-RQ*TFIX)*(N(d1)-1.0)
def calib_ratio(sig):   # K/S₀ 비율 (리셋 시 w=150%)
    f=lambda x: (1.0-put_delta(100.0,100.0*x,sig))-1.5
    return brentq(f,0.7,1.4)

def series(sheet,colidx):
    """xlsx는 '달력기준'(주말·휴일 forward-fill) → 실거래일만 추출:
    평일 필터 + 전일 대비 무변화(=휴일 fill) 행 제거"""
    raw=pd.read_excel(XLS,sheet_name=sheet,header=None)
    d=raw.iloc[14:]
    dt=pd.to_datetime(d.iloc[:,0]); px=pd.to_numeric(d.iloc[:,colidx],errors='coerce')
    s=pd.Series(px.values,index=dt.values).dropna()
    idx=pd.to_datetime(s.index)
    s=s[idx.dayofweek<5]                                  # 평일만
    chg=s.pct_change().fillna(1.0)
    s=s[chg!=0]                                            # 휴일 forward-fill 제거
    return s

def backtest(px,sig,label,tag):
    px=px.iloc[-253:]                      # 최근 1년(252영업일 수익률)
    dts=pd.to_datetime(px.index); S=px.values.astype(float)
    ASOF=pd.Timestamp(dts[-1]).strftime('%Y-%m-%d'); START=pd.Timestamp(dts[0]).strftime('%Y-%m-%d')
    kr=calib_ratio(sig)
    n=len(S); rday=RQ/252
    # 상태
    V={'p1':1.0,'p2':1.0,'bm':1.0}; navs={k:[1.0] for k in V}
    S0=S[0]; K=S0*kr
    def w1(s): return min(max(1.5-K_STD*(s/S0-1.0),1.0),2.0)
    def w2(s): return min(max(1.0-put_delta(s,K,sig),1.0),2.0)
    w={'p1':w1(S[0]),'p2':w2(S[0]),'bm':1.5}
    ww={'p1':[w['p1']],'p2':[w['p2']]}; resets=[]
    for t in range(1,n):
        r=S[t]/S[t-1]-1.0
        for k in V:
            V[k]*=1.0+w[k]*r+(1.0-w[k])*rday          # 주식수익 + 현금/차입(r=2.5%)
        if t%RESET==0:                                 # 분기 리셋: 기준 재설정 → 150% 복귀
            S0=S[t]; K=S0*kr; resets.append(dts[t])
        nw={'p1':w1(S[t]),'p2':w2(S[t]),'bm':1.5}
        for k in ('p1','p2'):
            V[k]-=TC*abs(nw[k]-w[k])*V[k]
        w=nw
        for k in V: navs[k].append(V[k])
        ww['p1'].append(w['p1']); ww['p2'].append(w['p2'])
    res={k:np.array(v) for k,v in navs.items()}
    base=S/S[0]
    def stats(nav):
        ret=(nav[-1]-1)*100
        dr=np.diff(nav)/nav[:-1]; vol=dr.std()*math.sqrt(252)*100
        mdd=((nav/np.maximum.accumulate(nav))-1).min()*100
        return ret,vol,mdd
    print(f"\n===== {label} 백테스트 ({START} ~ {ASOF}, 1년) · 상품2 K/S₀={kr*100:.1f}% =====")
    print(f"{'':14}{'수익률':>9}{'연변동성':>9}{'MDD':>9}")
    for nm,nav in (('기초 1배',base),('BM 150% 고정',res['bm']),('상품1 룰베이스',res['p1']),('상품2 옵션복제',res['p2'])):
        a,b,c=stats(np.asarray(nav)); print(f"{nm:14}{a:+8.1f}%{b:8.1f}%{c:+8.1f}%")
    print(f"편입비 범위: 상품1 {min(ww['p1'])*100:.0f}~{max(ww['p1'])*100:.0f}% · 상품2 {min(ww['p2'])*100:.0f}~{max(ww['p2'])*100:.0f}%")
    to1=np.abs(np.diff(ww['p1'])).sum()/ (n/252); to2=np.abs(np.diff(ww['p2'])).sum()/(n/252)
    print(f"연간 턴오버(편입비 변경 합): 상품1 {to1*100:.0f}%p · 상품2 {to2*100:.0f}%p")
    # ---- 차트: NAV + 편입비 ----
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(8.6,6.4),dpi=105,height_ratios=[1.7,1],sharex=True)
    ax1.plot(dts,base*100,color=SKY,lw=1.8,label='기초 1배')
    ax1.plot(dts,res['bm']*100,color=GRAY,lw=1.8,ls='--',label='BM 150% 고정')
    ax1.plot(dts,res['p1']*100,color=NAVY,lw=2.2,label='상품1 룰베이스(k=1.25)')
    ax1.plot(dts,res['p2']*100,color=ORANGE,lw=2.2,label='상품2 옵션복제(T=0.25 고정)')
    for rd in resets: ax1.axvline(rd,color='#ddd',lw=0.9)
    ax1.axhline(100,color='#9db4cc',lw=0.8)
    for nav,col in ((res['p1'],NAVY),(res['p2'],ORANGE),(res['bm'],GRAY),(base,SKY)):
        v=np.asarray(nav)[-1]*100
        ax1.annotate(f'{v-100:+.0f}%',xy=(dts[-1],v),xytext=(5,0),textcoords='offset points',color=col,fontsize=11,fontweight='bold',va='center')
    ax1.set_xlim(dts[0],dts[-1]+pd.Timedelta(days=16))
    ax1.set_ylabel('NAV (시작=100)',color=NAVY,fontsize=11.5)
    ax1.set_title(f'{label} — 오픈형 변동성 하베스트 실측 백테스트 (최근 1년)',color=NAVY,fontsize=14,fontweight='bold',loc='left',pad=10)
    ax1.legend(fontsize=9.5,frameon=False,loc='upper left'); ax1.grid(alpha=0.2)
    ax1.spines[['top','right']].set_visible(False)
    ax2.plot(dts,np.array(ww['p1'])*100,color=NAVY,lw=1.8,label='상품1 편입비')
    ax2.plot(dts,np.array(ww['p2'])*100,color=ORANGE,lw=1.8,label='상품2 편입비')
    for rd in resets: ax2.axvline(rd,color='#ddd',lw=0.9)
    for y in (100,150,200): ax2.axhline(y,color='#e5e5e5',lw=0.8,ls='--' if y==150 else ':')
    ax2.set_ylim(90,210); ax2.set_ylabel('편입비 (%)',color=NAVY,fontsize=11)
    ax2.legend(fontsize=9.5,frameon=False,loc='upper left'); ax2.grid(alpha=0.2)
    ax2.spines[['top','right']].set_visible(False)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%y/%m'))
    fig.text(0.98,0.012,f'데이터 기준일: {ASOF} ({START}~{ASOF}) · σ가정 {int(sig*100)}% · 분기(63영업일) 리셋(회색선) · 거래비용 15bps · r=2.5% · 가격수익률(배당 미반영)',
             ha='right',color=GRAY,fontsize=7.8)
    fig.tight_layout(rect=[0,0.03,1,1])
    fig.savefig(os.path.join(IMG,f'open_bt_{tag}.png')); plt.close(fig)
    print(f"saved open_bt_{tag}.png")

k200=series('코스피_코스피200_코스닥150',8)
hyx =series('삼성전자_하이닉스',8)
backtest(k200,0.50,'KOSPI200','k200')
backtest(hyx, 0.60,'SK하이닉스','hynix')
