# -*- coding: utf-8 -*-
"""1페이지(투자포인트) 중간 카드 '하락 방어' 임팩트 미니 차트 2장
- 지수(y=x, 회색)와 전략 구간평균(MC 1만회, σ60%, 19·20p와 동일 규칙)을 겹치고
  하락 구간(X<0)의 방어폭을 음영 + 화살표 + 수치로 강조
- 슬롯 3.04×1.42in (aspect 2.14) → figsize (6.5, 3.04)
"""
import os, platform, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np
from scipy.special import ndtr as N
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; RED='#C0392B'
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'img')

SIG=0.60; R,Q=0.025,0.025; T=1.0; DAYS=252
TCB,TCS=0.0005,0.0030; WMIN=0.10
KPUT,KKO,H,K1,K2=100.,100.,60.,110.,140.
NP=10000; SEED=20260728

def bs_delta(t,S,K,tau):
    sq=SIG*np.sqrt(tau); d1=(np.log(S/K)+0.5*SIG*SIG*tau)/sq
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
        V*=1.0+w*r0+(1.0-w)*rday
        if kind=='g': alive&= S>H
        tau=max(T-step*dt,1e-8)
        nw=(w_growth(S,tau,alive) if kind=='g' else w_stable(S,tau))
        V*=1.0-np.where(nw>w,TCB,TCS)*np.abs(nw-w)
        w=nw
    V*=1.0-TCS*w
    return (S/100.0-1.0)*100,(V-1.0)*100

def draw(kind,label,color,fname):
    X,Y=simulate(kind)
    lo,hi=-40,40
    edges=np.arange(lo,hi+2.5,2.5); cen=(edges[:-1]+edges[1:])/2
    bm=np.full(len(cen),np.nan)
    for b in range(len(cen)):
        sel=(X>=edges[b])&(X<edges[b+1])
        if sel.sum()>=15: bm[b]=Y[sel].mean()
    ok=~np.isnan(bm)
    v30=float(np.interp(-30,cen[ok],bm[ok]))
    print(f"[{label}] 지수 -30% 구간 전략 평균 {v30:+.1f}% (방어 {v30+30:+.0f}%p)")
    fig,ax=plt.subplots(figsize=(6.5,3.04),dpi=150)
    # 지수(y=x)와 전략 평균선, 하락 구간 방어폭 음영
    xs=cen[ok]; ys=bm[ok]
    ax.plot([lo,hi],[lo,hi],color='#93a4b8',lw=2.0,ls='--',label='지수')
    ax.plot(xs,ys,color=color,lw=3.2,label=label,solid_capstyle='round')
    mneg=xs<=0
    ax.fill_between(xs[mneg],xs[mneg],ys[mneg],color=color,alpha=0.16,lw=0)
    ax.axhline(0,color='#8a97a8',lw=0.8)
    # 임팩트 화살표: 지수 -30% vs 전략
    ax.annotate('',xy=(-30,v30),xytext=(-30,-30),
                arrowprops=dict(arrowstyle='-|>,head_width=0.5,head_length=1.0',color=RED,lw=2.6))
    mid=(v30-30)/2
    bb=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=0.75)
    ax.text(-28,mid+3.0,f"방어 {v30+30:+.0f}%p",color=RED,fontsize=15.5,fontweight='bold',va='center',bbox=bb)
    ax.text(-28,mid-4.5,f"지수 -30% → 전략 {v30:+.0f}%",color=color,fontsize=11.5,fontweight='bold',va='center',bbox=bb)
    ax.set_xlim(lo,hi); ax.set_ylim(-45,45)
    ax.set_xticks(range(-40,41,20))
    ax.set_xticklabels([f'{v:+d}%' if v else '0%' for v in range(-40,41,20)],fontsize=11)
    ax.set_yticks(range(-40,41,20))
    ax.set_yticklabels([f'{v:+d}%' if v else '0%' for v in range(-40,41,20)],fontsize=11)
    ax.grid(alpha=0.22)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=11,frameon=False,loc='lower right',handlelength=1.6)
    ax.text(0.02,0.96,label,transform=ax.transAxes,fontsize=13,fontweight='bold',color=color,va='top')
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)

draw('g','성장변동성펀드',ORANGE,'mini_defense_growth.png')
draw('s','안정변동성펀드',NAVY,'mini_defense_stable.png')
print("done")
