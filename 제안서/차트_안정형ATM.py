# -*- coding: utf-8 -*-
"""수익구조② 안정변동성펀드 scatter (v2 제안서 13페이지용)
- ATM 풋매도 복제(복제비율 100%), KO 없음 → 단일 분포
- σ60% · r=2.5% · q=2.5% · T=1년 · 매매비용 매수 5bp/매도 30bp · 일별 동적헤지 MC
- X=기초자산 등락률 −40~+40%, Y=구조화 수익 −20~+30%, 10% 눈금·등간격(equal aspect)
"""
import os, platform, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np
from scipy.special import ndtr as N
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'img')

SIG=0.60; R=0.025; Q=0.025; T=1.0; TCB,TCS=0.0005,0.0030; K=100.0; nP=7000
def bs_put(S,K_,T_):
    sq=SIG*np.sqrt(T_); d1=(np.log(S/K_)+(R-Q+0.5*SIG*SIG)*T_)/sq; d2=d1-sq
    return K_*np.exp(-R*T_)*N(-d2)-S*np.exp(-Q*T_)*N(-d1)
def put_delta(S,T_):
    sq=SIG*np.sqrt(T_); d1=(np.log(S/K)+(R-Q+0.5*SIG*SIG)*T_)/sq
    return np.exp(-Q*T_)*(N(d1)-1.0)

days=252; dt=T/days
rng=np.random.default_rng(20260727)
S=np.full(nP,100.0)
P0=float(bs_put(np.array([100.0]),K,T)[0])
h=-put_delta(S,T)                     # 숏풋 헤지 편입비
cash=(-P0)-h*100.0
tc=np.zeros(nP)
drift=(R-Q)-0.5*SIG*SIG; vol=SIG*np.sqrt(dt)
for step in range(1,days+1):
    S=S*np.exp(drift*dt+vol*rng.standard_normal(nP))
    tau=max(T-step*dt,1e-8)
    cash=cash*np.exp(R*dt)+h*S*Q*dt
    nh=-put_delta(S,tau); d=nh-h
    cost=np.where(d>0,TCB,TCS)*np.abs(d)*S
    cash-=d*S+cost; tc+=cost; h=nh
port=h*S+cash
payoff=-np.maximum(K-S,0.0)
hedgePnl=(port+tc)-payoff
pnlUnit=P0*np.exp(R*T)-np.maximum(K-S,0.0)
Y=(pnlUnit-tc+hedgePnl)/100.0*100.0   # 구조화 수익(%) = 이론손익 − 비용 + 복제오차
X=(S/100.0-1.0)*100.0                  # 기초자산 등락률(%)
print(f"ATM풋 프리미엄 {P0:.2f}% · 평균수익 {Y.mean():+.2f}% · 수익확률 {(Y>=0).mean()*100:.0f}% · 손익분기 지수 약 {-(P0*np.exp(R*T)):.1f}%")

fig,ax=plt.subplots(figsize=(9.6,6.35),dpi=115)
m=(X>=-40)&(X<=40)&(Y>=-20)&(Y<=30)
ax.axhline(0,color='#8a97a8',lw=0.9)
ax.axvline(0,color='#9aa7b8',ls='--',lw=1)
ax.scatter(X[m],Y[m],s=4,color=NAVY,alpha=0.35,linewidths=0)
# 구간 평균선
edges=np.linspace(-40,40,33); cen=(edges[:-1]+edges[1:])/2
bm=np.full(32,np.nan)
for b in range(32):
    sel=(X>=edges[b])&(X<edges[b+1])
    if sel.sum()>=5: bm[b]=np.clip(Y[sel].mean(),-20,30)
ax.plot(cen,bm,color=ORANGE,lw=2.4,label='구간 평균')
ax.set_xlim(-40,40); ax.set_ylim(-20,30)
ax.set_xticks(range(-40,41,10)); ax.set_yticks(range(-20,31,10))
ax.set_xticklabels([f'{v:+d}%' if v!=0 else '0%' for v in range(-40,41,10)],fontsize=11)
ax.set_yticklabels([f'{v:+d}%' if v!=0 else '0%' for v in range(-20,31,10)],fontsize=11)
ax.set_aspect('equal')                 # 10% 간격 X·Y 동일 길이
ax.set_xlabel('기초자산 가격 (리밸런싱일 대비 등락률)',fontsize=11.5,color=NAVY)
ax.set_ylabel('구조화 수익 (%)',fontsize=11.5,color=NAVY)
ax.grid(alpha=0.25)
ax.spines[['top','right']].set_visible(False)
ax.legend(fontsize=10,frameon=False,loc='upper left')
fig.tight_layout()
fig.savefig(os.path.join(IMG,'scat_stable_atm.png'),bbox_inches='tight')
print("saved scat_stable_atm.png")
