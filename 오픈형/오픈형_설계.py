# -*- coding: utf-8 -*-
"""오픈형 변동성 하베스트 레버리지 2종 설계 분석
설계 가정: 현 고변동 국면 반영, 지수 변동 범위 ±40%까지 가정 (±20% 아님)
상품1(룰베이스): w = 150% − k×(S/S₀−1), 캡 [100,200]
  - 표준 k=1.25 → ±40%에서 캡(100/200%) 도달
  - 공격 k=2.00 → ±25%에서 캡 도달 (레버리지ETF 미러, 비교용)
상품2(옵션복제): w = 100% + ATM급 풋매도 복제비중(고정만기 T=0.25, 행사가는 w₀=150% 역산)
  - σ50~60%·T0.25에서 ±40% 구간에 걸쳐 자연스럽게 100~200% 커버
공통: 오픈형 → 리밸런싱일마다 기준(S₀/K) 리셋 → 편입비 150% 복귀. 스무딩은 트랜치 롤링.
출력: 편입비 곡선/테이블(60~140), ±10% 민감도(vs 레버리지ETF +20%p 순응), 3개월 예상수익 곡선(MC)
"""
import os, platform, math, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np
from scipy.special import ndtr as N
from scipy.optimize import brentq
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; RED='#D02F00'; GRAY='#84888B'; GREEN='#1F9E6E'; CYAN='#0086B8'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img'); os.makedirs(IMG,exist_ok=True)

R,Q=0.03,0.02; TFIX=0.25   # 고정만기(상품2)

def put_delta(S,K,T,sig):   # BS 풋 델타 (배당 q)
    sq=sig*np.sqrt(T); d1=(np.log(S/K)+(R-Q+0.5*sig*sig)*T)/sq
    return np.exp(-Q*T)*(N(d1)-1.0)

# ---------- 편입비 규칙 ----------
def w_model1(S,S0=100,k=2.0):                 # 룰베이스(선형)
    return np.clip(1.5 - k*(S/S0-1.0), 1.0, 2.0)

def calib_K(sig,S0=100):                       # 상품2: 리셋 시 w=150% 되는 행사가 역산
    f=lambda K: (1.0+(-put_delta(S0,K,TFIX,sig)))-1.5
    return brentq(f,S0*0.7,S0*1.4)

def w_model2(S,K,sig):                         # 옵션복제(고정만기 풋매도 복제 오버레이)
    return np.clip(1.0+(-put_delta(S,K,TFIX,sig)), 1.0, 2.0)

# ---------- ① 편입비 곡선 + 테이블 ----------
K_STD=1.25   # 표준 기울기: ±40%에서 캡(100/200%) 도달

def chart_weights(sig,tag,label):
    K2=calib_K(sig)
    S=np.linspace(55,145,181)
    fig,ax=plt.subplots(figsize=(7.6,5.6),dpi=110)
    ax.plot(S,w_model1(S,k=2.0)*100,color=CYAN, lw=2.0,ls='--',label='상품1 룰베이스 (k=2.00, 공격·±25% 캡)')
    ax.plot(S,w_model1(S,k=K_STD)*100,color=NAVY, lw=2.6,label='상품1 룰베이스 (k=1.25, 표준·±40% 캡)')
    ax.plot(S,w_model2(S,K2,sig)*100,color=ORANGE,lw=2.6,label=f'상품2 옵션복제 (T=0.25 고정, σ{int(sig*100)}%)')
    for y in (100,150,200): ax.axhline(y,color='#ccc',lw=0.8,ls=':' if y!=150 else '--')
    ax.axvline(100,color='#9aa7b8',ls='--',lw=1)
    for xv in (60,140): ax.axvline(xv,color='#e3c9a8',ls=':',lw=1.2)
    ax.text(100,204,'리밸런싱일=100',color=GRAY,fontsize=9.5,ha='center')
    ax.text(60,95,'-40%',color='#c98a3d',fontsize=9,ha='center'); ax.text(140,95,'+40%',color='#c98a3d',fontsize=9,ha='center')
    ax.set_xlim(55,145); ax.set_ylim(92,212)
    ax.set_xlabel('지수 (리밸런싱일=100)',fontsize=11,color=NAVY)
    ax.set_ylabel('편입비 (%)',fontsize=11,color=NAVY)
    ax.set_title(f'{label} — 지수대별 편입비, ±40% 가정 (상승 시↓ · 하락 시↑)',fontsize=13,color=NAVY,fontweight='bold',loc='left')
    ax.grid(alpha=0.25); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=9.5,frameon=False,loc='upper right')
    fig.text(0.99,0.01,f'설계 가정: 지수 변동 ±40% · 상품2 행사가 K={K2:.1f} (시작 편입비 150% 역산) · r3%·q2%',ha='right',color=GRAY,fontsize=8.5)
    fig.tight_layout(rect=[0,0.03,1,1])
    fig.savefig(os.path.join(IMG,f'open_w_{tag}.png')); plt.close(fig)
    # 테이블 출력 (60~140, ±40%)
    rows=[60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140]
    print(f"\n[{label}] 편입비 테이블 (%) · ±40% 가정 · 상품2 K={K2:.1f}")
    print(f"{'지수':>5} | {'상품1 k=1.25':>11} | {'상품1 k=2':>9} | {'상품2 옵션복제':>12}")
    for m in rows:
        print(f"{m:5d} | {w_model1(np.array([m]),k=K_STD)[0]*100:11.1f} | {w_model1(np.array([m]),k=2.)[0]*100:9.1f} | {w_model2(np.array([m]),K2,sig)[0]*100:12.1f}")
    return K2

# ---------- ② ±10% 민감도 비교 ----------
def sensitivity(sig,K2,label):
    up1=(w_model1(np.array([110.]),k=K_STD)[0]-1.5)*100
    dn1=(w_model1(np.array([90.]),k=K_STD)[0]-1.5)*100
    up2=(w_model2(np.array([110.]),K2,sig)[0]-1.5)*100
    dn2=(w_model2(np.array([90.]),K2,sig)[0]-1.5)*100
    print(f"\n[{label}] ±10% 편입비 변동(150% 대비, %p): "
          f"레버리지ETF +10%시 +20/−10%시 −20(순응) | 상품1(k=1.25) {up1:+.1f}/{dn1:+.1f} | 상품2 {up2:+.1f}/{dn2:+.1f} (역방향)")
    return up1,dn1,up2,dn2

def chart_sensitivity(sens50,sens60):
    fig,ax=plt.subplots(figsize=(7.6,5.0),dpi=110)
    cats=['레버리지 ETF(2x)\n순응매매','상품1 룰베이스\n(k=1.25)','상품2 옵션복제\n(σ50%)','상품2 옵션복제\n(σ60%)']
    up=[+20,sens50[0],sens50[2],sens60[2]]
    dn=[-20,sens50[1],sens50[3],sens60[3]]
    x=np.arange(4); w=0.36
    b1=ax.bar(x-w/2,up,w,color=RED if True else RED,label='지수 +10% 시')
    b2=ax.bar(x+w/2,dn,w,color=NAVY,label='지수 −10% 시')
    b1[0].set_color('#E67E22'); b2[0].set_color('#B03A2E')
    for b in list(b1)+list(b2):
        v=b.get_height()
        ax.text(b.get_x()+b.get_width()/2, v+(1.2 if v>=0 else -2.6), f'{v:+.1f}%p', ha='center',fontsize=10,fontweight='bold',
                color='#333')
    ax.axhline(0,color='#888',lw=1)
    ax.set_xticks(x); ax.set_xticklabels(cats,fontsize=10.5)
    ax.set_ylabel('편입비 변동 (%p)',fontsize=11,color=NAVY)
    ax.set_title('지수 ±10% 시 편입비 변동 — 레버리지 ETF(순응) vs 본 펀드(역방향)',fontsize=13,color=NAVY,fontweight='bold',loc='left')
    ax.grid(axis='y',alpha=0.25); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=10.5,frameon=False,loc='lower left')
    fig.text(0.99,0.01,'레버리지 ETF: +10%→NAV의 약 20% 종가 추가매수(고가매수). 본 펀드는 반대로 상승 시 매도·하락 시 매수(저가매수·고가매도).',
             ha='right',color=GRAY,fontsize=8.2)
    fig.tight_layout(rect=[0,0.03,1,1])
    fig.savefig(os.path.join(IMG,'open_sensitivity.png')); plt.close(fig)

# ---------- ③ 3개월 예상수익 곡선 (MC, 일별 룰 적용) ----------
def mc_quarter(sig,K2,nP=6000,days=63,tc=0.0015,seed=20260715):
    dt=1/252; rng=np.random.default_rng(seed)
    S=np.full(nP,100.0)
    V1=np.ones(nP); V2=np.ones(nP); VB=np.ones(nP)      # 상품1, 상품2, BM150 고정
    w1=np.full(nP,1.5); w2=np.full(nP,1.5); wB=1.5
    for t in range(days):
        z=rng.standard_normal(nP)
        ret=np.exp((R-Q- 0.5*sig*sig)*dt+sig*np.sqrt(dt)*z)-1.0   # 가격수익률(위험중립)
        tr=ret+Q*dt                                                # 총수익(배당 포함)
        for V,w in ((V1,w1),(V2,w2),(VB,np.full(nP,wB))):
            V*=1.0+w*tr+(1.0-w)*R*dt
        S*=1.0+ret
        nw1=w_model1(S,k=K_STD); nw2=w_model2(S,K2,sig)
        V1-=tc*np.abs(nw1-w1)*V1; V2-=tc*np.abs(nw2-w2)*V2         # 거래비용
        w1,w2=nw1,nw2
    return S,(V1-1)*100,(V2-1)*100,(VB-1)*100

def chart_mc(sig,K2,tag,label):
    S,r1,r2,rB=mc_quarter(sig,K2)
    fig,ax=plt.subplots(figsize=(7.6,5.6),dpi=110)
    edges=np.linspace(60,150,31); cen=(edges[:-1]+edges[1:])/2
    for Y,col,nm in ((rB,'#9DB4CC','BM (150% 고정)'),(r1,NAVY,'상품1 룰베이스(k=1.25)'),(r2,ORANGE,'상품2 옵션복제')):
        bm=np.full(30,np.nan)
        for b in range(30):
            sel=(S>=edges[b])&(S<edges[b+1])
            if sel.sum()>=8: bm[b]=Y[sel].mean()
        ax.plot(cen,bm,color=col,lw=2.4,label=nm)
    ax.axhline(0,color='#888',lw=0.8); ax.axvline(100,color='#9aa7b8',ls='--',lw=1)
    ax.set_xlabel('3개월 후 지수 (리밸런싱일=100)',fontsize=11,color=NAVY)
    ax.set_ylabel('펀드 수익률 (%, 3개월)',fontsize=11,color=NAVY)
    ax.set_title(f'{label} — 지수대별 예상 수익률 (3개월, 구간평균)',fontsize=13.5,color=NAVY,fontweight='bold',loc='left')
    ax.grid(alpha=0.25); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=10.5,frameon=False,loc='upper left')
    fig.text(0.99,0.01,f'MC 6,000 paths · σ{int(sig*100)}% · 일별 룰 적용 · 거래비용 15bps · 자금조달 r=3% · 시뮬레이션 예시',
             ha='right',color=GRAY,fontsize=8.5)
    fig.tight_layout(rect=[0,0.03,1,1])
    fig.savefig(os.path.join(IMG,f'open_mc_{tag}.png')); plt.close(fig)
    # 통계
    for Y,nm in ((r1,'상품1'),(r2,'상품2'),(rB,'BM150')):
        print(f"  [{label} {nm}] 평균 {Y.mean():+.2f}% · σ {Y.std():.2f}% · 5%VaR {np.percentile(Y,5):+.2f}% · 승률 {(Y>=0).mean()*100:.0f}%")

if __name__=='__main__':
    print("="*80)
    K50=chart_weights(0.50,'k200','KOSPI200 (σ50%)')
    K60=chart_weights(0.60,'stock','삼성전자·하이닉스 (σ60%)')
    s50=sensitivity(0.50,K50,'σ50%'); s60=sensitivity(0.60,K60,'σ60%')
    chart_sensitivity(s50,s60)
    print()
    chart_mc(0.50,K50,'k200','KOSPI200 (σ50%)')
    chart_mc(0.60,K60,'stock','삼성전자·하이닉스 (σ60%)')
    print("\ncharts →", IMG)
