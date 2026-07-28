# -*- coding: utf-8 -*-
"""19·20페이지 우측: 실측 데이터 수익률 확률분포 (매 영업일 기산 1년 운용)
- 기초: 엑셀 D열 TOP2 지수(삼성·하이닉스 50:50 일별리밸)
- 매 영업일 종가를 기준가 100으로 1년 운용 (마지막 기산일 = 최신일-1년, 2025-07-28)
- 운용 규칙은 16~18페이지와 동일: σ=직전 60영업일 연환산(상한 60%), r=q=2.5%,
  편입비 하한 10% (성장 캡 180% / 안정 110%·캡 100%), 콜스프레드 110/140,
  매수 5bp/매도 30bp, +15% 달성 시 당일 종가 청산 후 같은 종가로 만기 1년 재세팅
- X=해당 1년 지수수익률 분포, Y=해당 1년 전략수익률 분포 (겹침 히스토그램)
"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
from scipy.special import ndtr as Nv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

R,Q=0.025,0.025; TCB,TCS=0.0005,0.0030
KPUT,KKO,H,K1,K2=100.,100.,60.,110.,140.
TARGET=0.15; SIGCAP=0.60; WMIN=0.10

raw=pd.read_excel(XLS,sheet_name='삼성전자_하이닉스',header=None)
d=raw.iloc[14:]
s=pd.Series(pd.to_numeric(d.iloc[:,3],errors='coerce').values,
            index=pd.to_datetime(d.iloc[:,0]).values).dropna()
i=pd.to_datetime(s.index); s=s[i.dayofweek<5]
chg=s.pct_change().fillna(1.0); top2=s[chg!=0]
ret=top2.pct_change().dropna(); dts=ret.index
px=(1.0+ret).cumprod()
lr=np.log(1+ret)
vol60=(lr.rolling(60,min_periods=60).std()*math.sqrt(252)).bfill().clip(upper=SIGCAP)

def N1(x): return float(Nv(x))
def bs_d(t,S,K,T,sig):
    sq=sig*math.sqrt(T); d1=(math.log(S/K)+(0.5*sig*sig)*T)/sq
    e=math.exp(-Q*T); return e*N1(d1) if t=='c' else e*(N1(d1)-1)
def bs_p(t,S,K,T,sig):
    sq=sig*math.sqrt(T); d1=(math.log(S/K)+(0.5*sig*sig)*T)/sq; d2=d1-sq
    e=math.exp(-Q*T); er=math.exp(-R*T)
    return S*e*N1(d1)-K*er*N1(d2) if t=='c' else K*er*N1(-d2)-S*e*N1(-d1)
def din(S,K,Hb,T,sig):
    b=R-Q; sq=sig*math.sqrt(T); mu=(b-0.5*sig*sig)/(sig*sig); phi=-1.; eta=1.
    x2=math.log(S/Hb)/sq+(1+mu)*sq; y1=math.log(Hb*Hb/(S*K))/sq+(1+mu)*sq; y2=math.log(Hb/S)/sq+(1+mu)*sq
    ebr=math.exp((b-R)*T); er=math.exp(-R*T); p1=(Hb/S)**(2*(mu+1)); p2=(Hb/S)**(2*mu)
    B=phi*S*ebr*N1(phi*x2)-phi*K*er*N1(phi*x2-phi*sq)
    C=phi*S*ebr*p1*N1(eta*y1)-phi*K*er*p2*N1(eta*y1-eta*sq)
    D=phi*S*ebr*p1*N1(eta*y2)-phi*K*er*p2*N1(eta*y2-eta*sq)
    return B-C+D
def dop(S,K,Hb,T,sig):
    if S<=Hb: return 0.0
    return max(bs_p('p',S,K,T,sig)-din(S,K,Hb,T,sig),0.0)
def ko_d(S,K,Hb,T,sig):
    if S<=Hb: return 0.0
    h=max(S*1e-4,1e-6); return (dop(S+h,K,Hb,T,sig)-dop(max(S-h,Hb+1e-9),K,Hb,T,sig))/(2*h)
def w_growth(S,tau,sig,alive):
    dd=-bs_d('p',S,KPUT,tau,sig)+(ko_d(S,KKO,H,tau,sig) if alive else 0.0) \
       +bs_d('c',S,K1,tau,sig)-bs_d('c',S,K2,tau,sig)
    return min(max(dd,WMIN),1.8)
def w_stable(S,tau,sig):
    return min(max(-bs_d('p',S,KPUT,tau,sig)*1.10,WMIN),1.0)

def run_year(kind,ia):
    """기산일 dts[ia] 종가=100 세팅, 1년 운용 (+15% 당일 종가 재운용 포함) → 1년 수익률"""
    rday=R/252
    ie=int(np.searchsorted(dts,dts[ia]+pd.Timedelta(days=365),side='right'))-1
    S=100.; V=1.; alive=True
    sig=max(float(vol60.iloc[ia]),0.05)
    mat=dts[ia]+pd.Timedelta(days=365)
    w=(w_growth(S,1.0,sig,True) if kind=='g' else w_stable(S,1.0,sig))
    V*=1.0-TCB*w; turnV0=V
    for j in range(ia+1,ie+1):
        r0=float(ret.iloc[j]); sig=max(float(vol60.iloc[j]),0.05)
        V*=1.0+w*r0+(1.0-w)*rday
        S*=1.0+r0
        if kind=='g' and alive and S<=H: alive=False
        if V/turnV0>=1.0+TARGET and j<ie:
            V*=1.0-TCS*w
            S=100.; alive=True; mat=dts[j]+pd.Timedelta(days=365)
            nw=(w_growth(S,1.0,sig,True) if kind=='g' else w_stable(S,1.0,sig))
            V*=1.0-TCB*nw; w=nw; turnV0=V
        else:
            tau=max((mat-dts[j]).days/365.0,1e-8)
            nw=(w_growth(S,tau,sig,alive) if kind=='g' else w_stable(S,tau,sig))
            V*=1.0-(TCB if nw>w else TCS)*abs(nw-w); w=nw
    V*=1.0-TCS*w                          # 1년 시점 전량 청산
    xr=float(px.iloc[ie]/px.iloc[ia]-1.0)
    return xr*100,(V-1.0)*100

anchors=[ia for ia in range(len(dts)) if dts[ia]+pd.Timedelta(days=365)<=dts[-1]]
print(f"기산일 {len(anchors)}회: {dts[anchors[0]].date()} ~ {dts[anchors[-1]].date()}")

def draw(kind,title,color,fname):
    X=[]; Y=[]
    for ia in anchors:
        xr,yr=run_year(kind,ia); X.append(xr); Y.append(yr)
    X=np.array(X); Y=np.array(Y)
    medX,medY=np.median(X),np.median(Y)
    mean=Y.mean(); pos=(Y>=0).mean()*100
    print(f"[{title}] 전략: 평균 {mean:+.1f}% · 중앙값 {medY:+.1f}% · 수익확률 {pos:.0f}% | 지수 중앙값 {medX:+.1f}%")
    lo,hi,bw=-80,200,5
    bins=np.arange(lo,hi+bw,bw)
    outX=((X<lo)|(X>hi)).mean()*100; outY=((Y<lo)|(Y>hi)).mean()*100
    n=len(X)
    fig,ax=plt.subplots(figsize=(8.97,6.5),dpi=125)
    ax.hist(np.clip(X,lo,hi),bins=bins,weights=np.full(n,100.0/n),
            color='#9db4cc',alpha=0.55,label='지수 1년 수익률 분포',edgecolor='white',linewidth=0.3)
    ax.hist(np.clip(Y,lo,hi),bins=bins,weights=np.full(n,100.0/n),
            color=color,alpha=0.60,label=f'{title} 1년 수익률 분포',edgecolor='white',linewidth=0.3)
    ax.axvline(0,color='#8a97a8',lw=0.9)
    ax.axvline(medX,color='#5c738c',ls='--',lw=1.6)
    ax.axvline(medY,color=color,ls='-',lw=2.0)
    ytop=ax.get_ylim()[1]
    ha1,ha2=('right','left') if medX<=medY else ('left','right')
    ax.text(medX,ytop*0.985,f'지수 중앙값 {medX:+.0f}%',color='#5c738c',fontsize=10.5,ha=ha1,va='top',fontweight='bold')
    ax.text(medY,ytop*0.92,f'전략 중앙값 {medY:+.0f}%',color=color,fontsize=10.5,ha=ha2,va='top',fontweight='bold')
    ax.set_xlim(lo,hi)
    ax.set_xticks(range(lo,hi+1,20))
    ax.set_xticklabels([f'{v:+d}%' if v else '0%' for v in range(lo,hi+1,20)],fontsize=10)
    ax.set_xlabel('1년 운용 수익률 (기산일 종가 대비)',fontsize=12,color=NAVY)
    ax.set_ylabel('기산일 비중 (%)',fontsize=12,color=NAVY)
    ax.set_title(f"{title} : 실측 분포 — 매 영업일 기산 1년 운용 ({len(anchors):,}회)",
                 fontsize=14,color=NAVY,fontweight='bold',loc='left',pad=10)
    ax.text(0.985,0.66,f"전략: 평균 {mean:+.1f}% · 중앙값 {medY:+.1f}% · 수익확률 {pos:.0f}%",
            transform=ax.transAxes,ha='right',va='top',fontsize=11,color=color,fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.35',fc='white',ec=color,lw=0.8,alpha=0.9))
    notes=[]
    if outX>0.05: notes.append(f"지수 {outX:.1f}%")
    if outY>0.05: notes.append(f"전략 {outY:.1f}%")
    if notes:
        ax.text(0.985,0.02,f"※ 표시범위(+200%) 초과 경로({' · '.join(notes)})는 우측 끝에 합산",
                transform=ax.transAxes,ha='right',va='bottom',fontsize=8.5,color=GRAY)
    ax.grid(alpha=0.25,axis='y')
    ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=10.5,frameon=False,loc='upper right',bbox_to_anchor=(0.99,0.80))
    fig.tight_layout()
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)

draw('g','성장변동성펀드',ORANGE,'dist_growth_real.png')
draw('s','안정변동성펀드',NAVY,'dist_stable_real.png')
print("done")
