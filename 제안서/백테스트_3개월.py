# -*- coding: utf-8 -*-
"""최근 3개월 급변동 구간 실측 (18페이지용) — 좌: 목표 환매 없음 / 우: +15% 재운용
- 기간: 2026-04-27 이후 첫 영업일 ~ 2026-07-27 (기준가=시작일 100, 만기 1년 지평)
- σ=직전 60영업일(주말 제외) 연율화 · r=q=2.5% · 매수 5bp/매도 30bp · 실거래일만
- 상단: 기초지수 vs 성장형·안정형 NAV / 하단: 두 전략 편입비(막대)
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
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#8fa8bf'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')
R,Q=0.025,0.025; TCB,TCS=0.0005,0.0030
KPUT,KKO,H,K1,K2=100.,100.,60.,110.,150.
START='2026-04-27'

def series(colidx):
    raw=pd.read_excel(XLS,sheet_name='삼성전자_하이닉스',header=None)
    d=raw.iloc[14:]
    s=pd.Series(pd.to_numeric(d.iloc[:,colidx],errors='coerce').values,
                index=pd.to_datetime(d.iloc[:,0]).values).dropna()
    idx=pd.to_datetime(s.index); s=s[idx.dayofweek<5]
    chg=s.pct_change().fillna(1.0); return s[chg!=0]
sam=series(4); hyx=series(8)
web_sam={'2026-07-13':254500,'2026-07-14':263000,'2026-07-15':279500,'2026-07-16':255000,
         '2026-07-20':244000,'2026-07-21':259000,'2026-07-22':260500,'2026-07-23':270000,
         '2026-07-24':249500,'2026-07-27':254000}
web_hyx={'2026-07-13':1845000,'2026-07-14':1913000,'2026-07-15':2082000,'2026-07-16':1842000,
         '2026-07-20':1764000,'2026-07-21':1836000,'2026-07-22':1830000,'2026-07-23':1919000,
         '2026-07-24':1759000,'2026-07-27':1816000}
sam=pd.concat([sam,pd.Series({pd.Timestamp(k):float(v) for k,v in web_sam.items()})])
hyx=pd.concat([hyx,pd.Series({pd.Timestamp(k):float(v) for k,v in web_hyx.items()})])
df=pd.concat([sam.rename('s'),hyx.rename('h')],axis=1).dropna().sort_index()
ret=(0.5*df['s'].pct_change()+0.5*df['h'].pct_change()).dropna()
dts=ret.index
lr=np.log(1+ret)
vol60=(lr.rolling(60,min_periods=60).std()*math.sqrt(252)).bfill()

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
    d=-bs_d('p',S,KPUT,tau,sig)+(ko_d(S,KKO,H,tau,sig) if alive else 0.0) \
      +bs_d('c',S,K1,tau,sig)-bs_d('c',S,K2,tau,sig)
    return min(max(d,0.0),1.8)
def w_stable(S,tau,sig):
    return min(max(-bs_d('p',S,KPUT,tau,sig),0.0)*1.10,1.0)

i0=int(np.searchsorted(dts,pd.Timestamp(START)))
i_end=len(dts)-1
rday=R/252; qday=Q/252
TARGET=0.15

def run(target_on):
    """3개월 구간. target_on=True: 턴 내 +15% 달성 시 종가 청산(30bp) → 다음날 현금 →
    그날 종가 재세팅(기준가·배리어·만기 1년, 재매수 5bp) → 익일부터 노출 (사용자 규칙)"""
    out={}
    for kind in ('g','s'):
        a0=i0-1                              # 앵커: 2026-04-24 종가 (노출은 4/27부터)
        mat=dts[a0]+pd.Timedelta(days=365)
        i_mat=int(np.searchsorted(dts,mat,side='right'))-1
        S=100.; V=1.; alive=True
        sig=max(float(vol60.iloc[a0]),0.05)
        w=(w_growth(S,(i_mat-a0)/252,sig,True) if kind=='g' else w_stable(S,(i_mat-a0)/252,sig))
        V*=1.0-TCB*w                         # 최초 매수
        turnV0=V
        pV=[100.]; pw=[w]; restarts=[]
        pending=False                        # 청산 후 현금 상태(다음날 재세팅 대기)
        for j in range(i0,i_end+1):
            r0=float(ret.iloc[j]); sig=max(float(vol60.iloc[j]),0.05)
            V*=1.0+w*(r0+qday)+(1.0-w)*rday
            S*=1.0+r0
            if kind=='g' and alive and S<=H: alive=False
            if pending:
                # 재세팅일 종가: 기준가=오늘 종가, 만기 1년, 배리어 리셋, 재매수
                S=100.; alive=True
                mat=dts[j]+pd.Timedelta(days=365)
                i_mat=int(np.searchsorted(dts,mat,side='right'))-1
                nw=(w_growth(S,(i_mat-j)/252,sig,True) if kind=='g' else w_stable(S,(i_mat-j)/252,sig))
                V*=1.0-TCB*nw
                w=nw; turnV0=V; pending=False
            else:
                tau=max((i_mat-j)/252,1e-8)
                nw=(w_growth(S,tau,sig,alive) if kind=='g' else w_stable(S,tau,sig))
                V*=1.0-(TCB if nw>w else TCS)*abs(nw-w)
                w=nw
                if target_on and V/turnV0>=1.0+TARGET and j<i_end:
                    restarts.append(dts[j])   # 달성일(종가 청산)
                    V*=1.0-TCS*w              # 전량 청산 비용
                    w=0.0; pending=True       # 다음날 현금
            pV.append(V*100); pw.append(w)
        out[kind]=dict(pV=np.array(pV),pw=np.array(pw),restarts=restarts)
    base=[100.]
    for j in range(i0,i_end+1): base.append(base[-1]*(1+float(ret.iloc[j])))
    dates=[dts[i0-1]]+list(dts[i0:i_end+1])
    return dates,np.array(base),out

def draw(dates,base,out,title,fname,show_restart):
    x=pd.to_datetime(dates)
    g,s=out['g'],out['s']
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(6.3,5.85),dpi=135,height_ratios=[1.5,1],sharex=True)
    ax1.plot(x,base,color=SKY,lw=1.8,label='기초지수(시작=100)')
    ax1.plot(x,g['pV'],color=ORANGE,lw=2.1,label='성장변동성펀드')
    ax1.plot(x,s['pV'],color=NAVY,lw=2.1,label='안정변동성펀드')
    ax1.axhline(100,color='#c9d5e2',lw=0.9)
    if show_restart:
        for kind,col in (('g',ORANGE),('s',NAVY)):
            pv=out[kind]['pV']
            for k,rd in enumerate(out[kind]['restarts'],1):
                ax1.axvline(rd,color=col,ls=':',lw=1.1,alpha=0.75)
                di=dates.index(rd); yv=pv[di]
                ax1.plot([rd],[yv],marker='*',ms=13,color=col,mec='white',mew=0.8,zorder=6)
                ax1.annotate(f"+15% 달성({rd.strftime('%m/%d')})",xy=(rd,yv),xytext=(-4,12),
                             textcoords='offset points',color=col,fontsize=7.8,fontweight='bold',ha='right')
    labs=sorted([(base[-1],SKY),(g['pV'][-1],ORANGE),(s['pV'][-1],NAVY)],key=lambda t:-t[0])
    yoff=[]
    for v,col in labs:
        yy=v
        while any(abs(yy-o)<9 for o in yoff): yy-=9
        yoff.append(yy)
        ax1.annotate(f"{v-100:+.1f}%",xy=(x[-1],yy),xytext=(4,0),textcoords='offset points',
                     color=col,fontsize=10,fontweight='bold',va='center')
    ax1.set_xlim(x[0],x[-1]+pd.Timedelta(days=8))
    ax1.set_title(title,fontsize=12,color=NAVY,fontweight='bold',loc='left')
    ax1.set_ylabel('수익률 (시작=100)',color=NAVY,fontsize=10)
    ax1.legend(fontsize=8.3,frameon=False,loc='upper left')
    ax1.grid(alpha=0.22); ax1.spines[['top','right']].set_visible(False)
    ax1.tick_params(labelsize=8.5)
    # 편입비 막대 (그룹)
    xg=pd.to_datetime(dates)
    off=pd.Timedelta(hours=9)
    ax2.bar(xg-off,g['pw']*100 if len(g['pw'])==len(xg) else np.append(g['pw'],g['pw'][-1])*100,
            width=0.34,color=ORANGE,alpha=0.85,label='성장형 편입비')
    ax2.bar(xg+off,s['pw']*100 if len(s['pw'])==len(xg) else np.append(s['pw'],s['pw'][-1])*100,
            width=0.34,color=NAVY,alpha=0.85,label='안정형 편입비')
    for yv in (50,100,150): ax2.axhline(yv,color='#e8edf2',lw=0.8,ls='--' if yv==100 else ':')
    if show_restart:
        for kind,col in (('g',ORANGE),('s',NAVY)):
            for rd in out[kind]['restarts']:
                ax2.axvline(rd,color=col,ls=':',lw=1.1,alpha=0.75)
    ax2.set_ylim(0,190); ax2.set_ylabel('편입비 (%)',color=NAVY,fontsize=9.5)
    ax2.legend(fontsize=8.3,frameon=False,loc='upper left')
    ax2.grid(alpha=0.2,axis='y'); ax2.spines[['top','right']].set_visible(False)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax2.tick_params(labelsize=8.5)
    note='점선(수직)=목표 +15% 달성 후 재운용 시점' if show_restart else ''
    fig.text(0.99,0.01,note,ha='right',color=GRAY,fontsize=7.5)
    fig.tight_layout(rect=[0,0.02,1,1])
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)

dates,base,out0=run(False)
print(f"[환매없음] 기초 {base[-1]-100:+.1f}% · 성장 {out0['g']['pV'][-1]-100:+.1f}% · 안정 {out0['s']['pV'][-1]-100:+.1f}%")
draw(dates,base,out0,'① 목표 환매 없음 (계속 운용)','qpms_3m.png',False)
dates,base,out1=run(True)
rg=[d.strftime('%m/%d') for d in out1['g']['restarts']]; rs=[d.strftime('%m/%d') for d in out1['s']['restarts']]
print(f"[+15% 재운용] 기초 {base[-1]-100:+.1f}% · 성장 {out1['g']['pV'][-1]-100:+.1f}% (재운용 {rg}) · 안정 {out1['s']['pV'][-1]-100:+.1f}% (재운용 {rs})")
draw(dates,base,out1,'② 목표 +15% 달성 시 재운용','qpms_3m_re.png',True)
