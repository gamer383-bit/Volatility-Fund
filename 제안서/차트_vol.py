# -*- coding: utf-8 -*-
"""제안서 3페이지 변동성 차트 2종 생성 (vol_kospi200.png / vol_semi.png)
- data/삼성전자_하이닉스_..._최근5년_주가데이터.xlsx 에서 계산
- 변동성 = 60영업일 일간수익률(로그) 표준편차 × √252 (연율화)
- '현재' 대신 데이터 기준일(마지막 영업일)을 표기, 백분위(%ile) 표기 없음
"""
import os, platform
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False

NAVY='#043B72'; ORANGE='#F58220'; DRED='#C0392B'; GRAY='#84888B'; LORANGE='#FDEBD9'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')
WIN=60; ANN=np.sqrt(252)

def series(sheet,colidx):
    """xlsx는 '달력기준'(주말·휴일 forward-fill) → 실거래일만 추출.
    (정정: 기존에는 수익률 0인 fill 행이 33% 섞여 변동성이 ~0.83배로 희석됐음)"""
    raw=pd.read_excel(XLS,sheet_name=sheet,header=None)
    d=raw.iloc[14:]
    dt=pd.to_datetime(d.iloc[:,0]); px=pd.to_numeric(d.iloc[:,colidx],errors='coerce')
    s=pd.Series(px.values,index=dt.values).dropna()
    idx=pd.to_datetime(s.index)
    s=s[idx.dayofweek<5]                       # 평일만
    chg=s.pct_change().fillna(1.0)
    return s[chg!=0]                            # 휴일 forward-fill 제거

def rollvol(s):
    r=np.log(s/s.shift(1)).dropna()
    return (r.rolling(WIN).std()*ANN*100).dropna()

k200=rollvol(series('코스피_코스피200_코스닥150',8))
sam =rollvol(series('삼성전자_하이닉스',4))
hyx =rollvol(series('삼성전자_하이닉스',8))
ASOF=pd.Timestamp(k200.index[-1]).strftime('%Y-%m-%d')
CAP=f"변동성 = 최근 {WIN}영업일 일간수익률 표준편차 × √252 연율화 · 데이터: 최근 5년 주가(2021.07~{ASOF})"

def style_ax(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color('#999')
    ax.tick_params(colors='#555',labelsize=13)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(axis='y',color='#eee',lw=0.8)
    ax.set_axisbelow(True)

# ---------- ① KOSPI200 ----------
fig,ax=plt.subplots(figsize=(14,6.3),dpi=100)
avg=k200.mean(); cur=k200.iloc[-1]
x=pd.to_datetime(k200.index)
ax.fill_between(x,k200.values,avg,where=(k200.values>avg),color=LORANGE,alpha=0.9,lw=0)
ax.plot(x,k200.values,color=NAVY,lw=2.2)
ax.axhline(avg,color='#888',ls='--',lw=1.3)
ax.text(x[int(len(x)*0.02)],avg+1.2,f'5년 평균 {avg:.1f}%',color=GRAY,fontsize=15)
ax.plot([x[-1]],[cur],'o',color='#CB3B00',ms=11)
ax.annotate(f'{ASOF} 기준\n{cur:.1f}%',xy=(x[-1],cur),xytext=(-185,-62),textcoords='offset points',
            color='#CB3B00',fontsize=17,fontweight='bold')
ax.set_title('KOSPI200 실현변동성 — 최근 5년 중 최고 수준',color=NAVY,fontsize=19,fontweight='bold',loc='left',pad=14)
ax.set_ylabel(f'연율화 실현변동성 (%, {WIN}영업일)',color=NAVY,fontsize=15)
style_ax(ax)
fig.text(0.995,0.01,CAP,ha='right',color=GRAY,fontsize=11.5)
fig.tight_layout(rect=[0,0.03,1,1])
fig.savefig(os.path.join(IMG,'vol_kospi200.png')); plt.close(fig)

# ---------- ② 삼성전자·SK하이닉스 ----------
fig,ax=plt.subplots(figsize=(14,6.3),dpi=100)
xs=pd.to_datetime(sam.index); xh=pd.to_datetime(hyx.index)
# 최근 급등 구간 음영 (마지막 2개월)
t1=xh[-1]; t0=t1-pd.Timedelta(days=60)
ax.axvspan(t0,t1,color=LORANGE,alpha=0.75,lw=0)
ax.plot(xh,hyx.values,color=DRED,lw=2.2,label='SK하이닉스')
ax.plot(xs,sam.values,color=ORANGE,lw=2.2,label='삼성전자')
ah,as_=hyx.mean(),sam.mean()
ax.axhline(ah,color=DRED,ls=':',lw=1.2,alpha=0.7)
ax.axhline(as_,color=ORANGE,ls=':',lw=1.2,alpha=0.7)
ax.text(xh[int(len(xh)*0.03)],ah+1.5,f'SK 5년평균 {ah:.0f}%',color=DRED,fontsize=13.5,alpha=0.85)
ax.text(xs[int(len(xs)*0.03)],as_-4.5,f'삼성 5년평균 {as_:.0f}%',color=ORANGE,fontsize=13.5,alpha=0.85)
ax.plot([xh[-1]],[hyx.iloc[-1]],'o',color=DRED,ms=10)
ax.plot([xs[-1]],[sam.iloc[-1]],'o',color=ORANGE,ms=10)
ax.annotate(f'SK하이닉스 {hyx.iloc[-1]:.0f}%  ({ASOF} 기준)',xy=(xh[-1],hyx.iloc[-1]),xytext=(-330,18),
            textcoords='offset points',color=DRED,fontsize=17,fontweight='bold')
ax.annotate(f'삼성전자 {sam.iloc[-1]:.0f}%',xy=(xs[-1],sam.iloc[-1]),xytext=(-215,-48),
            textcoords='offset points',color=ORANGE,fontsize=17,fontweight='bold')
ax.text(t0+pd.Timedelta(days=4),ax.get_ylim()[0]+6,'최근\n역대급 급등',color=ORANGE,fontsize=13,fontweight='bold')
ax.set_title('삼성전자·SK하이닉스 실현변동성 — 역대급 확대',color=NAVY,fontsize=19,fontweight='bold',loc='left',pad=14)
ax.set_ylabel(f'연율화 실현변동성 (%, {WIN}영업일)',color=NAVY,fontsize=15)
ax.legend(fontsize=14,frameon=False,loc='upper left')
style_ax(ax)
fig.text(0.995,0.01,CAP,ha='right',color=GRAY,fontsize=11.5)
fig.tight_layout(rect=[0,0.03,1,1])
fig.savefig(os.path.join(IMG,'vol_semi.png')); plt.close(fig)

print(f"asof={ASOF} | K200 cur={cur:.1f}% avg={avg:.1f}% | SK {hyx.iloc[-1]:.0f}%/{ah:.0f}% | 삼성 {sam.iloc[-1]:.0f}%/{as_:.0f}%")
print("saved vol_kospi200.png, vol_semi.png")
