# -*- coding: utf-8 -*-
"""채권혼합 ETF 운용 방식 비교 (동일 조건: TOP2, σ상한 70%, 주식 배분 50%, 매수5bp/매도30bp)
A. 분기 리셋(현행): 행사가 분기 고정 + 만기 3개월→0으로 감소, 분기말 전량 청산(30bp)·재세팅(5bp)
B. 상시 3개월(τ=0.25 고정): 행사가는 분기마다 리셋, 만기는 매일 3개월 유지, 분기말 전량 청산 없음
C. (참고) 매일 전체 리셋: 행사가=당일 지수·τ=0.25 → 델타가 거의 상수(사실상 고정 편입비)
"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
from scipy.special import ndtr as Nv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; GREEN='#1F9E6E'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

SIG=0.70; R,Q=0.025,0.025; T=0.25
KP,K1,K2=100.,110.,150.
WMIN,WMAX=0.10,1.00; ALLOC=0.50; TCB,TCS=0.0005,0.0030
SIGCAP=0.70

def N1(x): return float(Nv(x))
def bsd(t,S,K,tau,sig):
    sq=sig*math.sqrt(tau); d1=(math.log(S/K)+0.5*sig*sig*tau)/sq
    e=math.exp(-Q*tau); return e*N1(d1) if t=='c' else e*(N1(d1)-1)
def sdelta(S,tau,sig):
    d=-bsd('p',S,KP,tau,sig)+bsd('c',S,K1,tau,sig)-bsd('c',S,K2,tau,sig)
    return min(max(d,WMIN),WMAX)

raw=pd.read_excel(XLS,sheet_name='삼성전자_하이닉스',header=None)
d=raw.iloc[14:]
s=pd.Series(pd.to_numeric(d.iloc[:,3],errors='coerce').values,index=pd.to_datetime(d.iloc[:,0]).values).dropna().sort_index()
ii=pd.to_datetime(s.index); s=s[ii.dayofweek<5]
chg=s.pct_change().fillna(1.0); top2=s[chg!=0]
ret=top2.pct_change().dropna(); dts=ret.index
lr=np.log(1+ret)
vol60=(lr.rolling(60,min_periods=60).std()*math.sqrt(252)).bfill().clip(upper=SIGCAP)
rday=R/252
i0=int(np.searchsorted(dts,pd.Timestamp('2021-07-28'))); i1=len(dts)-1

def run(mode):
    V=1.0; S=100.
    sig=max(float(vol60.iloc[i0]),0.05)
    mat=dts[i0]+pd.Timedelta(days=91)
    w=sdelta(100.,T,sig)*ALLOC; V*=1.0-TCB*w
    dsl=[dts[i0]]; navs=[V]; ws=[w]; cost=TCB*w
    for j in range(i0+1,i1+1):
        r0=float(ret.iloc[j]); sig=max(float(vol60.iloc[j]),0.05)
        V*=1.0+w*r0+(1.0-w)*rday; S*=1.0+r0
        if mode=='C':
            nw=sdelta(100.,T,sig)*ALLOC                     # 매일 행사가·만기 리셋
            c=(TCB if nw>w else TCS)*abs(nw-w); V*=1.0-c; cost+=c; w=nw
        elif dts[j]>=mat and j<i1:                          # 분기 경계
            if mode=='A':
                c=TCS*w; V*=1.0-c; cost+=c                  # 전량 청산
                S=100.; nw=sdelta(100.,T,sig)*ALLOC
                c=TCB*nw; V*=1.0-c; cost+=c; w=nw
            else:                                           # B: 행사가만 리셋(차액 리밸)
                S=100.; nw=sdelta(100.,T,sig)*ALLOC
                c=(TCB if nw>w else TCS)*abs(nw-w); V*=1.0-c; cost+=c; w=nw
            mat=dts[j]+pd.Timedelta(days=91)
        else:
            tau=(max((mat-dts[j]).days/365.0,1e-8) if mode=='A' else T)   # A: 감소 / B: 0.25 고정
            nw=sdelta(S,tau,sig)*ALLOC
            c=(TCB if nw>w else TCS)*abs(nw-w); V*=1.0-c; cost+=c; w=nw
        dsl.append(dts[j]); navs.append(V); ws.append(w)
    return pd.DatetimeIndex(dsl),np.array(navs),np.array(ws),cost

def stats(nm,dl,nav,ws,cost,bm=None):
    yrs=(dl[-1]-dl[0]).days/365.25
    tot=nav[-1]-1; cagr=nav[-1]**(1/yrs)-1
    dr=pd.Series(nav).pct_change().dropna()
    vol=dr.std()*math.sqrt(252)
    mdd=(pd.Series(nav)/pd.Series(nav).cummax()-1).min()
    i3=int(np.searchsorted(dl,pd.Timestamp('2026-04-30'),side='right'))-1
    r3=nav[-1]/nav[i3]-1
    print(f"[{nm}] 누적 {tot*100:+7.1f}% · 연환산 {cagr*100:+5.1f}% · 변동성 {vol*100:4.1f}% · MDD {mdd*100:5.1f}% · 최근3개월 {r3*100:+5.1f}% · 누적 매매비용 {cost*100:.1f}%p · 평균 편입비 {ws.mean()*100:.1f}%")
    return tot,cagr,vol,mdd,r3

dlA,navA,wA,cA=run('A')
dlB,navB,wB,cB=run('B')
dlC,navC,wC,cC=run('C')
bm=np.ones(len(dlA)); base=top2.loc[dlA]/top2.loc[dlA[0]]
for k in range(1,len(dlA)):
    bm[k]=bm[k-1]*(1+0.4*float(base.iloc[k]/base.iloc[k-1]-1)+0.6*rday)
print(f"기간 {dlA[0].date()} ~ {dlA[-1].date()}\n")
stats('A. 분기 리셋(현행)   ',dlA,navA,wA,cA)
stats('B. 상시 3개월(τ고정)',dlB,navB,wB,cB)
stats('C. 매일 전체 리셋    ',dlC,navC,wC,cC)
yrs=(dlA[-1]-dlA[0]).days/365.25
drB=pd.Series(bm).pct_change().dropna()
mddB=(pd.Series(bm)/pd.Series(bm).cummax()-1).min()
i3=int(np.searchsorted(dlA,pd.Timestamp('2026-04-30'),side='right'))-1
print(f"[BM (40/60 매일 리밸)  ] 누적 {(bm[-1]-1)*100:+7.1f}% · 연환산 {(bm[-1]**(1/yrs)-1)*100:+5.1f}% · 변동성 {drB.std()*math.sqrt(252)*100:4.1f}% · MDD {mddB*100:5.1f}% · 최근3개월 {(bm[-1]/bm[i3]-1)*100:+5.1f}%")

fig,(ax1,ax2)=plt.subplots(2,1,figsize=(10.5,6.6),dpi=140,height_ratios=[1.7,1],sharex=True)
ax1.plot(dlA,bm*100,color=GRAY,lw=1.5,ls='--',label='BM (TOP2 40%+1년국고채)')
ax1.plot(dlA,navA*100,color=ORANGE,lw=2.2,label='A. 분기 리셋 (만기 3개월→0 감소)')
ax1.plot(dlB,navB*100,color=NAVY,lw=2.0,label='B. 상시 3개월 (τ=0.25 고정)')
ax1.plot(dlC,navC*100,color=GREEN,lw=1.6,ls=':',label='C. 매일 전체 리셋 (참고)')
ax1.axhline(100,color='#c9d5e2',lw=0.8)
for v,c in ((bm[-1]*100,GRAY),(navA[-1]*100,ORANGE),(navB[-1]*100,NAVY),(navC[-1]*100,GREEN)):
    ax1.annotate(f"{v-100:+.1f}%",xy=(dlA[-1],v),xytext=(4,0),textcoords='offset points',color=c,fontsize=9.5,fontweight='bold',va='center')
ax1.set_xlim(dlA[0],dlA[-1]+pd.Timedelta(days=60))
ax1.set_title('운용 방식 비교 — 분기 리셋 vs 상시 3개월 (TOP2 · 2021-07-28~2026-07-30 · 주식 50%)',
              fontsize=13,color=NAVY,fontweight='bold',loc='left')
ax1.legend(fontsize=9,frameon=False,loc='upper left')
ax1.grid(alpha=0.22); ax1.spines[['top','right']].set_visible(False)
ax2.plot(dlA,wA*100,color=ORANGE,lw=1.1,alpha=0.9,label='A 편입비')
ax2.plot(dlB,wB*100,color=NAVY,lw=1.1,alpha=0.9,label='B 편입비')
ax2.axhline(50,color='#c05000',ls=':',lw=0.9)
ax2.set_ylim(0,55); ax2.set_ylabel('주식 편입비(%)',fontsize=9,color=NAVY)
ax2.legend(fontsize=8.5,frameon=False,loc='lower left',ncols=2)
ax2.grid(alpha=0.2); ax2.spines[['top','right']].set_visible(False)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
fig.tight_layout()
fig.savefig(os.path.join(IMG,'compare_reset_vs_rolling.png'),bbox_inches='tight'); plt.close(fig)
print("\nsaved compare_reset_vs_rolling.png")
