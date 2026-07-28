# -*- coding: utf-8 -*-
"""QPMS 별첨(성장/안정) 5턴 백테스트 — AI Top2 동일가중, 1년 단위, 마지막 턴 2026-07-27 종료
조건: 실거래일만(주말 포지션·수익률 변동 없음) · σ=직전 60영업일 연환산 실현변동성(초기 확장창 최소 10일)
      r=q=2.5% 고정 · 매매비용 매수 5bp/매도 30bp · 성장형(참여 100%, 캡 180%, 풋100+KO60+콜스프레드110/150)
      안정형(ATM 풋매도, 참여 110%, 캡 100%)
데이터: xlsx(~2026-07-10, 실거래일 정제) + 2026-07-13~07-27 Yahoo Finance 실측
      (검증: 6/30·7/8~10 xlsx 일치, 7/24 종가 = 진입청사진 249,500/1,759,000 일치, 7/17 휴장)
"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
from scipy.special import ndtr as Nv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#8fa8bf'; HDRBG='#E9F0F8'; BLUE='#2E5F97'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

R,Q=0.025,0.025; TCB,TCS=0.0005,0.0030
KPUT,KKO,H,K1,K2=100.,100.,60.,110.,150.

def series(colidx):
    raw=pd.read_excel(XLS,sheet_name='삼성전자_하이닉스',header=None)
    d=raw.iloc[14:]
    s=pd.Series(pd.to_numeric(d.iloc[:,colidx],errors='coerce').values,
                index=pd.to_datetime(d.iloc[:,0]).values).dropna()
    idx=pd.to_datetime(s.index); s=s[idx.dayofweek<5]
    chg=s.pct_change().fillna(1.0); return s[chg!=0]
sam=series(4); hyx=series(8)
# ---- 2026-07-13 ~ 07-27 실측 보강 (Yahoo Finance, 7/17 휴장) ----
web_sam={'2026-07-13':254500,'2026-07-14':263000,'2026-07-15':279500,'2026-07-16':255000,
         '2026-07-20':244000,'2026-07-21':259000,'2026-07-22':260500,'2026-07-23':270000,
         '2026-07-24':249500,'2026-07-27':254000}
web_hyx={'2026-07-13':1845000,'2026-07-14':1913000,'2026-07-15':2082000,'2026-07-16':1842000,
         '2026-07-20':1764000,'2026-07-21':1836000,'2026-07-22':1830000,'2026-07-23':1919000,
         '2026-07-24':1759000,'2026-07-27':1816000}
sam=pd.concat([sam,pd.Series({pd.Timestamp(k):float(v) for k,v in web_sam.items()})])
hyx=pd.concat([hyx,pd.Series({pd.Timestamp(k):float(v) for k,v in web_hyx.items()})])
df=pd.concat([sam.rename('s'),hyx.rename('h')],axis=1).dropna().sort_index()
ret=0.5*df['s'].pct_change()+0.5*df['h'].pct_change()          # Top2 동일가중 일수익률
ret=ret.dropna()
dts=ret.index
print(f"Top2 시계열: {dts[0].date()} ~ {dts[-1].date()} ({len(ret)}영업일)")

# ---- 롤링 60일 연환산 변동성 (초기 확장창 최소 10일) ----
lr=np.log(1+ret)
vol60=(lr.rolling(60,min_periods=10).std()*math.sqrt(252)).bfill()   # 초기 미충족 구간은 최초 유효치(≈10일차) 백필

# ---- 옵션 델타 (r=q=2.5) ----
def N1(x): return float(Nv(x))
def bs_p(t,S,K,T,sig):
    sq=sig*math.sqrt(T); d1=(math.log(S/K)+(0.5*sig*sig)*T)/sq; d2=d1-sq
    e=math.exp(-Q*T); er=math.exp(-R*T)
    return S*e*N1(d1)-K*er*N1(d2) if t=='c' else K*er*N1(-d2)-S*e*N1(-d1)
def bs_d(t,S,K,T,sig):
    sq=sig*math.sqrt(T); d1=(math.log(S/K)+(0.5*sig*sig)*T)/sq
    e=math.exp(-Q*T); return e*N1(d1) if t=='c' else e*(N1(d1)-1)
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
    d=-bs_d('p',S,KPUT,tau,sig)+ (ko_d(S,KKO,H,tau,sig) if alive else 0.0) \
      +bs_d('c',S,K1,tau,sig)-bs_d('c',S,K2,tau,sig)
    return min(max(d,0.0),1.8)
def w_stable(S,tau,sig):
    return min(max(-bs_d('p',S,KPUT,tau,sig),0.0)*1.10,1.0)

# ---- 턴 경계: 매년 7/27 이하 마지막 영업일 종료, 5턴 ----
ends=[]
for y in (2022,2023,2024,2025,2026):
    ends.append(dts[dts<=pd.Timestamp(f'{y}-07-27')][-1])
starts=[dts[0]]
for e in ends[:-1]:
    starts.append(dts[dts>e][0])
print("턴 경계:",[f"{s.date()}~{e.date()}" for s,e in zip(starts,ends)])

def run_turn(kind, s_dt, e_dt):
    """kind: 'g' 성장 / 's' 안정. 반환: 기초등락, 펀드수익, 경로(지수·NAV·편입비), 배리어터치일"""
    win=ret.loc[s_dt:e_dt]
    n=len(win); rday=R/252; qday=Q/252
    S=100.0; V=1.0; alive=True; touch=None
    sig0=max(float(vol60.loc[:s_dt].iloc[-2]) if len(vol60.loc[:s_dt])>1 else 0.4,0.05)
    tau0=n/252
    w=(w_growth(S,tau0,sig0,True) if kind=='g' else w_stable(S,tau0,sig0))
    path_S=[S]; path_V=[100.0]; path_w=[w]
    for i,(d,r0) in enumerate(win.items(),1):
        V*=1.0+w*(r0+qday)+(1.0-w)*rday
        S*=1.0+r0
        if kind=='g' and alive and S<=H: alive=False; touch=d
        tau=max((n-i)/252,1e-8)
        sig=max(float(vol60.loc[d]),0.05)
        nw=(w_growth(S,tau,sig,alive) if kind=='g' else w_stable(S,tau,sig))
        cost=(TCB if nw>w else TCS)*abs(nw-w)
        V-=cost*V; w=nw
        path_S.append(S); path_V.append(V*100); path_w.append(w)
    return S/100-1, V-1, np.array(path_S), np.array(path_V), np.array(path_w), touch

results={}
for kind,nm in (('g','성장형'),('s','안정형')):
    rows=[]
    for k,(s_dt,e_dt) in enumerate(zip(starts,ends),1):
        b,f,pS,pV,pw,touch=run_turn(kind,s_dt,e_dt)
        rows.append(dict(turn=k,s=s_dt,e=e_dt,base=b,fund=f,pS=pS,pV=pV,pw=pw,touch=touch))
        tt=f" 배리어터치 {touch.date()}" if touch is not None else ""
        print(f"[{nm}] 턴{k} {s_dt.date()}~{e_dt.date()}: 기초 {b*100:+.1f}% / 펀드 {f*100:+.1f}%{tt}")
    results[kind]=rows

# ---- 턴 요약 테이블 PNG (기존 카드 스타일) ----
def draw_table(kind,fname,prod_label,with_barrier):
    rows=results[kind]
    ncol=5 if with_barrier else 4
    fig,ax=plt.subplots(figsize=(7.6,2.85),dpi=150)
    ax.axis('off')
    # 카드 배경
    fig.patch.set_facecolor('white')
    ax.add_patch(plt.Rectangle((0.005,0.02),0.99,0.96,fill=False,ec='#d5dde6',lw=1.4,
                 transform=ax.transAxes,clip_on=False,joinstyle='round'))
    ax.text(0.03,0.90,'턴 요약',transform=ax.transAxes,fontsize=13,fontweight='bold',color=NAVY)
    cols=['턴','기간','기초 등락',prod_label]+(['배리어'] if with_barrier else [])
    xs=[0.03,0.10,0.52,0.70,0.86][:ncol]
    y0=0.74; dy=0.115
    for j,(c,x) in enumerate(zip(cols,xs)):
        ax.text(x,y0,c,transform=ax.transAxes,fontsize=10.5,fontweight='bold',color=BLUE)
    ax.plot([0.02,0.98],[y0-0.035,y0-0.035],transform=ax.transAxes,color='#c9d5e2',lw=1.2)
    for i,r in enumerate(rows):
        y=y0-dy*(i+1)
        vals=[str(r['turn']),f"{r['s'].date()} ~ {r['e'].date()}",f"{r['base']*100:+.1f}%",f"{r['fund']*100:+.1f}%"]
        if with_barrier: vals.append(f"도달({r['touch'].strftime('%y.%m.%d')})" if r['touch'] is not None else "미도달")
        for j,(v,x) in enumerate(zip(vals,xs)):
            ax.text(x+0.10 if j in (2,3) else x, y, v, transform=ax.transAxes, fontsize=10,
                    color=(NAVY if j==3 else '#333333'),
                    ha=('right' if j in (2,3) else 'left'), fontweight=('bold' if j==3 else 'normal'))
        if i<len(rows)-1:
            ax.plot([0.02,0.98],[y-0.045,y-0.045],transform=ax.transAxes,color='#eef2f6',lw=0.9)
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight',facecolor='white'); plt.close(fig)
    print("saved",fname)
draw_table('g','qpms_table_g.png','상품1(성장형)',True)
draw_table('s','qpms_table_s.png','상품2(안정형)',False)

# ---- 예시 그래프: 하락기 턴 / 상승기 턴 ----
def pick_turns(kind):
    rows=results[kind]
    down=min(rows,key=lambda r:r['base'])
    up=max(rows,key=lambda r:r['base'])
    return down,up
def draw_turn(kind,r,fname,label,color):
    x=np.arange(len(r['pS']))
    fig,ax=plt.subplots(figsize=(7.4,3.16),dpi=150)
    ax2=ax.twinx()
    ax2.fill_between(x,r['pw']*100,color=color,alpha=0.12,lw=0)
    ax2.set_ylim(0,200); ax2.set_yticks([0,50,100,150,200])
    ax2.set_yticklabels(['0%','','100%','','200%'],fontsize=8,color=GRAY)
    ax.plot(x,r['pS'],color=SKY,lw=1.6,label='기초지수(시작=100)')
    ax.plot(x,r['pV'],color=color,lw=2.0,label='펀드 NAV')
    ax.axhline(100,color='#c9d5e2',lw=0.8)
    if r['touch'] is not None:
        ti=list(ret.loc[r['s']:r['e']].index).index(r['touch'])+1
        ax.axvline(ti,color='#D02F00',ls='--',lw=1.1)
        ax.text(ti,ax.get_ylim()[0],' 배리어 도달',color='#D02F00',fontsize=8.5,va='bottom')
    ax.set_title(f"{label} — 턴{r['turn']} ({r['s'].date()} ~ {r['e'].date()})  기초 {r['base']*100:+.1f}% / 펀드 {r['fund']*100:+.1f}%",
                 fontsize=11,color=NAVY,fontweight='bold',loc='left')
    ax.set_xlabel('영업일차',fontsize=9,color=NAVY)
    ax.legend(fontsize=8.5,frameon=False,loc='upper left')
    ax.grid(alpha=0.2); ax.spines[['top']].set_visible(False)
    ax.tick_params(labelsize=9)
    fig.text(0.99,0.01,'음영=편입비(우축)',ha='right',color=GRAY,fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)
for kind,color in (('g',ORANGE),('s',NAVY)):
    down,up=pick_turns(kind)
    draw_turn(kind,down,f'qpms_down_{kind}.png','하락기 예시',color)
    draw_turn(kind,up,  f'qpms_up_{kind}.png','상승기 예시',color)
print("done")
