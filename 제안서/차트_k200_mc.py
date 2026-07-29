# -*- coding: utf-8 -*-
"""K200 제안서용 MC 차트 일괄 생성 (σ50% 가정, 현행 운용 규칙)
- 규칙: 편입비 하한 10% · 성장 풋100+KO60+콜스프레드110/140 캡180% · 안정 ATM풋×110% 캡100%
- r=q=2.5% · 매수5bp/매도30bp · 만기 청산 30bp · 만기 1년 · 일별 리밸런싱 · MC 1만회
산출물:
  scat_k2_growth_nt.png / scat_k2_growth_t.png  (10페이지: 미도달/도달 scatter)
  scat_k2_stable.png                            (12페이지: 안정형 scatter)
  mini_defense_growth_k2.png / mini_defense_stable_k2.png (1페이지 방어 카드)
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

SIG=0.50; R,Q=0.025,0.025; T=1.0; DAYS=252
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
    return S,(V-1.0)*100,(~alive if kind=='g' else np.zeros(NP,bool))

Sg,Yg,tg=simulate('g'); Ss,Ys,_=simulate('s')
Xg=Sg; Xs=(Ss/100-1)*100

def scatter(X,Y,title,color,xr,yr,fname,xstep,xlabel,figsize=(5.3,4.3),xf=None):
    fig,ax=plt.subplots(figsize=figsize,dpi=150)
    m=(X>=xr[0])&(X<=xr[1])&(Y>=yr[0])&(Y<=yr[1])
    if yr[0]<0<yr[1]: ax.axhline(0,color='#8a97a8',lw=0.8)
    ax.scatter(X[m],Y[m],s=3,color=color,alpha=0.35,linewidths=0)
    B=34; edges=np.linspace(xr[0],xr[1],B+1); cen=(edges[:-1]+edges[1:])/2
    bm=np.full(B,np.nan)
    for b in range(B):
        sel=(X>=edges[b])&(X<edges[b+1])
        if sel.sum()>=3: bm[b]=np.clip(Y[sel].mean(),yr[0],yr[1])
    ax.plot(cen,bm,color=ORANGE,lw=2.3,label='구간 평균')
    ax.set_xlim(*xr); ax.set_ylim(*yr)
    ax.set_xticks(np.arange(xr[0],xr[1]+1,xstep))
    if xf: ax.set_xticklabels([xf(v) for v in np.arange(xr[0],xr[1]+1,xstep)],fontsize=9)
    ax.set_xlabel(xlabel,fontsize=9.5,color=NAVY)
    ax.set_ylabel('실현 수익률 (%)',fontsize=9.5,color=NAVY)
    ax.set_title(title,fontsize=12,color=NAVY,fontweight='bold',loc='left')
    if xr[0]<100<xr[1] and xr[1]>150:
        ax.axvline(100,color='#9aa7b8',ls='--',lw=1)
        ax.text(100,yr[1],'S0=100',color=GRAY,fontsize=8,ha='center',va='top')
    if xr[0]<0<xr[1] and xr[1]<=50: ax.axvline(0,color='#9aa7b8',ls='--',lw=1)
    ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=9,frameon=False,loc='upper left')
    fig.tight_layout(); fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)

nt=~tg
print(f"[성장 σ50] 터치율 {tg.mean()*100:.1f}% · 미터치 평균 {Yg[nt].mean():+.1f}% · 터치 평균 {Yg[tg].mean():+.1f}%")
print(f"[안정 σ50] 평균 {Ys.mean():+.1f}% · 중앙값 {np.median(Ys):+.1f}% · 수익확률 {(Ys>=0).mean()*100:.0f}%")
scatter(Xg[nt],Yg[nt],'성장변동성펀드 — 운용 중 -40% 미도달',GREEN,(50,160),(-20,60),'scat_k2_growth_nt.png',10,'만기 기초자산 가격 (S0=100)')
scatter(Xg[tg],Yg[tg],'성장변동성펀드 — 운용 중 -40% 도달',RED,(50,160),(-30,60),'scat_k2_growth_t.png',10,'만기 기초자산 가격 (S0=100)')
scatter(Xs,Ys,'안정변동성펀드 — 안정 변동성 매매',NAVY,(-40,40),(-20,30),'scat_k2_stable.png',10,'기초자산 가격 (리밸런싱일 대비 등락률)',figsize=(9.6,6.35),xf=lambda v:f'{v:+.0f}%' if v else '0%')

# ---- 방어 미니 카드 2장 ----
def mini(kind,label,color,fname):
    S,Y,_=simulate(kind)
    X=(S/100-1)*100
    lo,hi=-40,40
    edges=np.arange(lo,hi+2.5,2.5); cen=(edges[:-1]+edges[1:])/2
    bm=np.full(len(cen),np.nan)
    for b in range(len(cen)):
        sel=(X>=edges[b])&(X<edges[b+1])
        if sel.sum()>=15: bm[b]=Y[sel].mean()
    ok=~np.isnan(bm); xs=cen[ok]; ys=bm[ok]
    v30=float(np.interp(-30,xs,ys))
    print(f"[{label}] 지수 -30% → 전략 {v30:+.1f}% (방어 {v30+30:+.0f}%p)")
    fig,ax=plt.subplots(figsize=(6.5,3.04),dpi=150)
    ax.plot([lo,hi],[lo,hi],color='#93a4b8',lw=2.0,ls='--',label='지수')
    ax.plot(xs,ys,color=color,lw=3.2,label=label,solid_capstyle='round')
    mneg=xs<=0
    ax.fill_between(xs[mneg],xs[mneg],ys[mneg],color=color,alpha=0.16,lw=0)
    ax.axhline(0,color='#8a97a8',lw=0.8)
    ax.annotate('',xy=(-30,v30),xytext=(-30,-30),
                arrowprops=dict(arrowstyle='-|>,head_width=0.5,head_length=1.0',color='#C0392B',lw=2.6))
    mid=(v30-30)/2
    bb=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=0.75)
    ax.text(-28,mid+3.0,f"방어 {v30+30:+.0f}%p",color='#C0392B',fontsize=15.5,fontweight='bold',va='center',bbox=bb)
    ax.text(-28,mid-4.5,f"지수 -30% → 전략 {v30:+.0f}%",color=color,fontsize=11.5,fontweight='bold',va='center',bbox=bb)
    ax.set_xlim(lo,hi); ax.set_ylim(-45,45)
    ax.set_xticks(range(-40,41,20)); ax.set_yticks(range(-40,41,20))
    ax.set_xticklabels([f'{v:+d}%' if v else '0%' for v in range(-40,41,20)],fontsize=11)
    ax.set_yticklabels([f'{v:+d}%' if v else '0%' for v in range(-40,41,20)],fontsize=11)
    ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=11,frameon=False,loc='lower right',handlelength=1.6)
    ax.text(0.02,0.96,label,transform=ax.transAxes,fontsize=13,fontweight='bold',color=color,va='top')
    fig.tight_layout(pad=0.4)
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)
mini('g','성장변동성펀드',ORANGE,'mini_defense_growth_k2.png')
mini('s','안정변동성펀드',NAVY,'mini_defense_stable_k2.png')
print("done")
