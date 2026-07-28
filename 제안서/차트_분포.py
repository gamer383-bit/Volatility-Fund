# -*- coding: utf-8 -*-
"""19·20페이지: 수익률 확률분포 산점도 (몬테카를로 1만회)
- X=만기 지수수익률, Y=전략(펀드) 수익률 · σ=60% 고정 · 만기 1년 · GBM(위험중립 r−q)
- 운용 규칙은 16~18페이지와 동일: 일별 구조화 편입비 리밸런싱,
  성장형 풋100+KO60+콜스프레드110/140 편입비[10%,180%], 안정형 ATM풋×110% [10%,100%]
- 회계: 주식분=주가수익률, 잔여분=현금 연 2.5% · 매수 5bp/매도 30bp · 만기 전량 청산 30bp
- 목표 환매(+15% 재운용) 미적용 — 1년 단일 구조의 분포
"""
import os, platform, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np
from scipy.special import ndtr as N
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; GREEN='#1F9E6E'; RED='#D02F00'
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'img')

SIG=0.60; R,Q=0.025,0.025; T=1.0; DAYS=252
TCB,TCS=0.0005,0.0030; WMIN=0.10
KPUT,KKO,H,K1,K2=100.,100.,60.,110.,140.
NP=10000; SEED=20260728

def bs_delta(t,S,K,tau):
    sq=SIG*np.sqrt(tau); d1=(np.log(S/K)+0.5*SIG*SIG*tau)/sq   # r=q → b=0
    e=np.exp(-Q*tau)
    return e*N(d1) if t=='c' else e*(N(d1)-1)
def bs_price(t,S,K,tau):
    sq=SIG*np.sqrt(tau); d1=(np.log(S/K)+0.5*SIG*SIG*tau)/sq; d2=d1-sq
    e=np.exp(-Q*tau); er=np.exp(-R*tau)
    return S*e*N(d1)-K*er*N(d2) if t=='c' else K*er*N(-d2)-S*e*N(-d1)
def din_put(S,K,Hb,tau):
    b=R-Q; sq=SIG*np.sqrt(tau); mu=(b-0.5*SIG*SIG)/(SIG*SIG); phi=-1.; eta=1.
    x2=np.log(S/Hb)/sq+(1+mu)*sq; y1=np.log(Hb*Hb/(S*K))/sq+(1+mu)*sq; y2=np.log(Hb/S)/sq+(1+mu)*sq
    ebr=np.exp((b-R)*tau); er=np.exp(-R*tau); p1=(Hb/S)**(2*(mu+1)); p2=(Hb/S)**(2*mu)
    B=phi*S*ebr*N(phi*x2)-phi*K*er*N(phi*x2-phi*sq)
    C=phi*S*ebr*p1*N(eta*y1)-phi*K*er*p2*N(eta*y1-eta*sq)
    D=phi*S*ebr*p1*N(eta*y2)-phi*K*er*p2*N(eta*y2-eta*sq)
    return B-C+D
def dop(S,K,Hb,tau):
    v=np.maximum(bs_price('p',S,K,tau)-din_put(S,K,Hb,tau),0.0)
    return np.where(S<=Hb,0.0,v)
def ko_delta(S,K,Hb,tau):
    h=np.maximum(S*1e-4,1e-6)
    return (dop(S+h,K,Hb,tau)-dop(np.maximum(S-h,Hb+1e-9),K,Hb,tau))/(2*h)

def w_growth(S,tau,alive):
    d=-bs_delta('p',S,KPUT,tau)+np.where(alive,ko_delta(S,KKO,H,tau),0.0) \
      +bs_delta('c',S,K1,tau)-bs_delta('c',S,K2,tau)
    return np.clip(d,WMIN,1.8)
def w_stable(S,tau):
    return np.clip(-bs_delta('p',S,KPUT,tau)*1.10,WMIN,1.0)

def simulate(kind):
    dt=T/DAYS; rday=R/252
    drift=(R-Q)-0.5*SIG*SIG; vol=SIG*np.sqrt(dt)
    rng=np.random.default_rng(SEED)
    S=np.full(NP,100.0); V=np.ones(NP); alive=np.ones(NP,bool)
    w=(w_growth(S,T,alive) if kind=='g' else w_stable(S,T))
    V*=1.0-TCB*w
    for step in range(1,DAYS+1):
        Sn=S*np.exp(drift*dt+vol*rng.standard_normal(NP))
        r0=Sn/S-1.0; S=Sn
        V*=1.0+w*r0+(1.0-w)*rday          # 주식분=주가수익률, 잔여분=현금 2.5%/년
        if kind=='g': alive&= S>H
        tau=max(T-step*dt,1e-8)
        nw=(w_growth(S,tau,alive) if kind=='g' else w_stable(S,tau))
        V*=1.0-np.where(nw>w,TCB,TCS)*np.abs(nw-w)
        w=nw
    V*=1.0-TCS*w                           # 만기 전량 청산
    X=(S/100.0-1.0)*100; Y=(V-1.0)*100
    return X,Y,(~alive if kind=='g' else np.zeros(NP,bool))

def draw(kind,title,fname):
    X,Y,touched=simulate(kind)
    med=np.median(Y); mean=Y.mean(); pos=(Y>=0).mean()*100
    p5,p95=np.percentile(Y,5),np.percentile(Y,95)
    print(f"[{title}] 평균 {mean:+.1f}% · 중앙값 {med:+.1f}% · 수익확률 {pos:.0f}% · 5~95% [{p5:+.1f}%, {p95:+.1f}%]"
          +(f" · 배리어 터치 {touched.mean()*100:.1f}%" if kind=='g' else ""))
    xlim=(-80,160); ylo=np.floor(np.percentile(Y,0.2)/10)*10; yhi=np.ceil(np.percentile(Y,99.8)/10)*10
    fig,ax=plt.subplots(figsize=(8.97,6.5),dpi=125)
    m=(X>=xlim[0])&(X<=xlim[1])&(Y>=ylo)&(Y<=yhi)
    ax.axhline(0,color='#8a97a8',lw=0.9)
    ax.axvline(0,color='#9aa7b8',ls='--',lw=1)
    if kind=='g':
        nt=~touched
        ax.scatter(X[m&nt],Y[m&nt],s=3.5,color=NAVY,alpha=0.30,linewidths=0,label=f'배리어 미터치 ({nt.mean()*100:.0f}%)')
        ax.scatter(X[m&touched],Y[m&touched],s=3.5,color=RED,alpha=0.30,linewidths=0,label=f'배리어(-40%) 터치 ({touched.mean()*100:.0f}%)')
    else:
        ax.scatter(X[m],Y[m],s=3.5,color=NAVY,alpha=0.28,linewidths=0)
    # 구간 평균선
    B=40; edges=np.linspace(xlim[0],xlim[1],B+1); cen=(edges[:-1]+edges[1:])/2
    bm=np.full(B,np.nan)
    for b in range(B):
        sel=(X>=edges[b])&(X<edges[b+1])
        if sel.sum()>=10: bm[b]=np.clip(Y[sel].mean(),ylo,yhi)
    ax.plot(cen,bm,color=ORANGE,lw=2.6,label='구간 평균')
    ax.set_xlim(*xlim); ax.set_ylim(ylo,yhi)
    ax.set_xticks(range(-80,161,20))
    ax.set_xticklabels([f'{v:+d}%' if v else '0%' for v in range(-80,161,20)],fontsize=10.5)
    ax.set_yticks(np.arange(ylo,yhi+1,10))
    ax.set_yticklabels([f'{v:+.0f}%' if v else '0%' for v in np.arange(ylo,yhi+1,10)],fontsize=10.5)
    ax.set_xlabel('만기 지수수익률 (설정일 대비)',fontsize=12,color=NAVY)
    ax.set_ylabel('전략 수익률 (%)',fontsize=12,color=NAVY)
    ax.set_title(f"{title} : 수익률 확률분포 (몬테카를로 1만회 · σ 60%)",
                 fontsize=14.5,color=NAVY,fontweight='bold',loc='left',pad=10)
    ax.text(0.985,0.03,f"평균 {mean:+.1f}% · 중앙값 {med:+.1f}% · 수익확률 {pos:.0f}%",
            transform=ax.transAxes,ha='right',va='bottom',fontsize=11,color=ORANGE,fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.35',fc='white',ec=ORANGE,lw=0.8,alpha=0.9))
    ax.grid(alpha=0.25)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=9.5,frameon=False,loc='upper left')
    fig.tight_layout()
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)

draw('g','성장변동성펀드','dist_growth.png')
draw('s','안정변동성펀드','dist_stable.png')
print("done")
