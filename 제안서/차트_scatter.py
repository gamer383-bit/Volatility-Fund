# -*- coding: utf-8 -*-
"""옵션복제 시뮬레이터 MC(동적헤지)를 파이썬 벡터화로 포팅 → 수익구조 scatter 생성.
안정변동성펀드=풋매도only, 성장변동성펀드=풋매도+KO풋+콜스프레드(배리어 터치/미터치)."""
import numpy as np
from scipy.special import ndtr as N  # 표준정규 CDF (벡터)

# ---------- Black-Scholes (벡터) ----------
def bs_price(typ,S,K,T,sig,r,q):
    sq=sig*np.sqrt(T)
    d1=(np.log(S/K)+(r-q+0.5*sig*sig)*T)/sq; d2=d1-sq
    eqt=np.exp(-q*T); ert=np.exp(-r*T)
    if typ=='c': return S*eqt*N(d1)-K*ert*N(d2)
    return K*ert*N(-d2)-S*eqt*N(-d1)
def bs_delta(typ,S,K,T,sig,r,q):
    sq=sig*np.sqrt(T)
    d1=(np.log(S/K)+(r-q+0.5*sig*sig)*T)/sq
    eqt=np.exp(-q*T)
    return eqt*N(d1) if typ=='c' else eqt*(N(d1)-1)

# ---------- 배리어 down-and-in put (K>H 가정: B-C+D) ----------
def din_put(S,K,H,T,sig,r,q):
    b=r-q; sq=sig*np.sqrt(T); mu=(b-0.5*sig*sig)/(sig*sig); phi=-1.0; eta=1.0
    x2=np.log(S/H)/sq+(1+mu)*sq
    y1=np.log(H*H/(S*K))/sq+(1+mu)*sq
    y2=np.log(H/S)/sq+(1+mu)*sq
    ebr=np.exp((b-r)*T); ert=np.exp(-r*T)
    pw1=(H/S)**(2*(mu+1)); pw2=(H/S)**(2*mu)
    B=phi*S*ebr*N(phi*x2)-phi*K*ert*N(phi*x2-phi*sq)
    C=phi*S*ebr*pw1*N(eta*y1)-phi*K*ert*pw2*N(eta*y1-eta*sq)
    D=phi*S*ebr*pw1*N(eta*y2)-phi*K*ert*pw2*N(eta*y2-eta*sq)
    return B-C+D
def down_out_put(S,K,H,T,sig,r,q):
    van=bs_price('p',S,K,T,sig,r,q); din=din_put(S,K,H,T,sig,r,q)
    val=np.maximum(van-din,0.0)
    return np.where(S<=H,0.0,val)
def ko_delta(S,K,H,tau,sig,r,q):
    h=np.maximum(S*1e-4,1e-6)
    return (down_out_put(S+h,K,H,tau,sig,r,q)-down_out_put(S-h,K,H,tau,sig,r,q))/(2*h)

# ---------- MC 동적헤지 ----------
def run_mc(sig, use_ko, use_spr, nP=6000, seed=20260513, w=1.0,
           S0=100.,T=1.,r=0.03,q=0.02,days=252,tc=0.0015,maxW=1.8,
           Kput=100.,Kko=100.,H=60.,K1=110.,K2=150.):
    nSteps=int(round(days*T)); dt=T/nSteps
    drift=(r-q)-0.5*sig*sig; vol=sig*np.sqrt(dt)
    rng=np.random.default_rng(seed)
    S=np.full(nP,S0)
    # 전략 목록 구성: 항상 put, 옵션으로 ko/spr
    strat=[]  # (kind, w)
    strat.append('put')
    if use_ko: strat.append('ko')
    if use_spr: strat.append('spr')
    # w = 복제비율 (기본 100%, 인자로 지정)
    def dlt(kind,S,tau):
        if kind=='put': return -bs_delta('p',S,Kput,tau,sig,r,q)*w
        if kind=='spr': return (bs_delta('c',S,K1,tau,sig,r,q)-bs_delta('c',S,K2,tau,sig,r,q))*w
        if kind=='ko':  return ko_delta(S,Kko,H,tau,sig,r,q)*w
    def price0(kind):
        if kind=='put': return -bs_price('p',S0,Kput,T,sig,r,q)*w
        if kind=='spr': return (bs_price('c',S0,K1,T,sig,r,q)-bs_price('c',S0,K2,T,sig,r,q))*w
        if kind=='ko':  return float(down_out_put(np.array([S0]),Kko,H,T,sig,r,q)[0])*w
    def prem0(kind):  # pnlUnit 기준 초기 프리미엄 (단위당 — 복제비율 w는 pnlUnit에서 1회만 적용)
        if kind=='put': return bs_price('p',S0,Kput,T,sig,r,q)
        if kind=='spr': return (bs_price('c',S0,K1,T,sig,r,q)-bs_price('c',S0,K2,T,sig,r,q))
        if kind=='ko':  return float(down_out_put(np.array([S0]),Kko,H,T,sig,r,q)[0])
    # 상태
    st={}
    for k in strat:
        d0=float(dlt(k,np.array([S0]),T)[0]); v0=price0(k)
        st[k]=dict(h=np.full(nP,d0), cash=np.full(nP,v0-d0*S0),
                   tc=np.zeros(nP), alive=np.ones(nP,bool), pr0=prem0(k))
    erT=np.exp(r*T)
    for step in range(1,nSteps+1):
        z=rng.standard_normal(nP)
        S=S*np.exp(drift*dt+vol*z)
        tau=max(T-step*dt,1e-8)
        # (1) 낙아웃 + 현금 carry
        for k in strat:
            H_=st[k]
            if k=='ko': H_['alive']=H_['alive']&(S>H)
            H_['cash']=H_['cash']*np.exp(r*dt)+H_['h']*S*q*dt
        # (2) 리밸런싱(freq=1 매스텝) — 총편입비 상한
        raw={}
        for k in strat:
            d=dlt(k,S,tau)
            if k=='ko': d=np.where(st[k]['alive'],d,0.0)
            raw[k]=d
        tot=sum(raw.values())
        atot=np.abs(tot); scale=np.where(atot>maxW, maxW/np.where(atot>maxW,atot,1.0),1.0)
        for k in strat:
            H_=st[k]; tgt=raw[k]*scale; dtrade=tgt-H_['h']; cost=tc*np.abs(dtrade)*S
            H_['cash']=H_['cash']-dtrade*S-cost; H_['h']=tgt; H_['tc']=H_['tc']+cost
    # 만기 정산
    dh_total=np.zeros(nP)
    for k in strat:
        H_=st[k]; alive=H_['alive']; port=H_['h']*S+H_['cash']
        if k=='put':
            payoff=-np.maximum(Kput-S,0)*w
            pnlUnit=(H_['pr0']*erT-np.maximum(Kput-S,0))*w
        elif k=='spr':
            pay=np.maximum(S-K1,0)-np.maximum(S-K2,0)
            payoff=pay*w; pnlUnit=(pay-H_['pr0']*erT)*w
        else: # ko
            pv=np.where(alive,np.maximum(Kko-S,0),0.0)
            payoff=pv*w; pnlUnit=(pv-H_['pr0']*erT)*w
        hedgePnl=(port+H_['tc'])-payoff
        fundRet=(pnlUnit-H_['tc'])/S0
        dhRet=fundRet+hedgePnl/S0
        dh_total+=dhRet
    X=S/S0*100.0; Y=dh_total*100.0
    touched=np.zeros(nP,bool)
    if 'ko' in strat: touched=~st['ko']['alive']
    return X,Y,touched

# ---------- scatter 플롯 ----------
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import platform
plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; RED='#D02F00'; GRAY='#84888B'; GREEN='#1F9E6E'; CYAN='#00A9CE'
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),"img")

def plot_scatter(X,Y,title,ptcolor,yr,fname,figsize=(5.3,4.3)):
    xmin,xmax=50,160
    m=(X>=xmin)&(X<=xmax)&(Y>=yr[0])&(Y<=yr[1])
    fig,ax=plt.subplots(figsize=figsize,dpi=150)
    ax.axvspan(xmin,xmax,color='none')
    # 0선, S0선
    if yr[0]<0<yr[1]: ax.axhline(0,color='#8a97a8',lw=0.8)
    ax.axvline(100,color='#9aa7b8',ls='--',lw=1); ax.text(100,yr[1],'S0=100',color=GRAY,fontsize=8,ha='center',va='top')
    ax.scatter(X[m],Y[m],s=3,color=ptcolor,alpha=0.35,linewidths=0)
    # 구간 평균선
    B=34; edges=np.linspace(xmin,xmax,B+1); cen=(edges[:-1]+edges[1:])/2
    bm=np.full(B,np.nan)
    for b in range(B):
        sel=(X>=edges[b])&(X<edges[b+1])
        if sel.sum()>=3: bm[b]=np.clip(Y[sel].mean(),yr[0],yr[1])
    ax.plot(cen,bm,color=ORANGE,lw=2.3,label='구간 평균')
    ax.set_xlim(xmin,xmax); ax.set_ylim(*yr)
    ax.set_xticks(range(50,161,10))
    ax.set_xlabel('만기 기초자산 가격 (S0=100)',fontsize=9.5,color=NAVY)
    ax.set_ylabel('실현 수익률 (%)',fontsize=9.5,color=NAVY)
    ax.set_title(title,fontsize=12,color=NAVY,fontweight='bold',loc='left')
    ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=9,frameon=False,loc='upper left')
    fig.tight_layout(); fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)

def build_fund(tag, sig, nP=7000, w_growth=1.0, w_stable=1.0):
    # 성장변동성펀드: put+KO+spread → 배리어 미터치/터치
    Xg,Yg,t=run_mc(sig,True,True,nP=nP,w=w_growth); nt=~t
    # 안정변동성펀드: put only
    Xs,Ys,_=run_mc(sig,False,False,nP=nP,w=w_stable)
    # Y범위: 미터치 [-20,60], 터치 [-30,60] (지정)
    ysr=(-30, max(np.ceil(np.percentile(Ys,99)/10)*10,30))  # 하단 -30% 고정
    plot_scatter(Xg[nt],Yg[nt],'성장변동성펀드 — 운용 중 -40% 미도달'+(f' · 복제비율 {int(w_growth*100)}%' if w_growth!=1.0 else ''),GREEN,(-20,60),f'scat_{tag}_growth_nt.png')
    plot_scatter(Xg[t], Yg[t], '성장변동성펀드 — 운용 중 -40% 도달'+(f' · 복제비율 {int(w_growth*100)}%' if w_growth!=1.0 else ''),   RED,  (-30,60),f'scat_{tag}_growth_t.png')
    plot_scatter(Xs,   Ys,    '안정변동성펀드 — 안정 변동성 매매'+(f' · 복제비율 {int(w_stable*100)}%' if w_stable!=1.0 else ''),       NAVY, ysr,   f'scat_{tag}_stable.png',figsize=(7.4,4.3))
    print(f"[{tag} σ{int(sig*100)}] 성장 터치 {t.mean()*100:.1f}% | 미터치평균 {Yg[nt].mean():+.1f}% 터치평균 {Yg[t].mean():+.1f}% | 안정평균 {Ys.mean():+.1f}% 수익확률 {(Ys>=0).mean()*100:.0f}%")

if __name__=='__main__':
    build_fund('kospi',0.50)
    build_fund('top2', 0.60, w_stable=1.10)   # Top2 덱: 안정형만 복제비율 110% (성장형 100%)
    print("scatter charts done")
