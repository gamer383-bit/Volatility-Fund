# -*- coding: utf-8 -*-
"""TOP2 변동성 하베스트 채권혼합 ETF — 제안서 자산 일괄 생성
이 펀드 전용 규칙(사용자 지정):
- 구조: ATM 풋매도(100) + 콜스프레드 매수(110/150), 만기 3개월 고정, 행사가 분기 리셋
- σ 상한 70% (MC 기본가정 σ=70%, 백테스트는 직전 60영업일 연환산 상한 70%)
- 약관: 채권(1년 국고채) 50% 이상 · 주식 및 주식파생 50% 이하 → 주식 배분 50%
- 편입비 = 구조화 델타 clip[10%,100%] × 50% · 잔여(채권·현금) 연 2.5% 가정
- BM = TOP2 40% + 1년 국고채 50% (+현금 10%), 오픈형(목표 환매 없음)
"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
from scipy.special import ndtr as Nv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch, Rectangle

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#8fa8bf'; BLUE='#2E5F97'; RED='#C0392B'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

SIG=0.70; R,Q=0.025,0.025; T=0.25
KP,K1,K2=100.,110.,150.
WMIN,WMAX=0.10,1.00; ALLOC=0.50; TCB,TCS=0.0005,0.0030
SIGCAP=0.70

def N1(x): return float(Nv(x))
def bsd(t,S,K,tau,sig=SIG):
    sq=sig*math.sqrt(tau); d1=(math.log(S/K)+0.5*sig*sig*tau)/sq
    e=math.exp(-Q*tau); return e*N1(d1) if t=='c' else e*(N1(d1)-1)
def bsp(t,S,K,tau,sig=SIG):
    sq=sig*math.sqrt(tau); d1=(math.log(S/K)+0.5*sig*sig*tau)/sq; d2=d1-sq
    e=math.exp(-Q*tau); er=math.exp(-R*tau)
    return S*e*N1(d1)-K*er*N1(d2) if t=='c' else K*er*N1(-d2)-S*e*N1(-d1)
def sdelta(S,tau,sig=SIG):
    d=-bsd('p',S,KP,tau,sig)+bsd('c',S,K1,tau,sig)-bsd('c',S,K2,tau,sig)
    return min(max(d,WMIN),WMAX)
def svalue(S,tau,sig=SIG):
    return -bsp('p',S,KP,tau,sig)+bsp('c',S,K1,tau,sig)-bsp('c',S,K2,tau,sig)
V0=svalue(100.,T)
def sret(S,tau):
    V=(-max(KP-S,0)+max(S-K1,0)-max(S-K2,0)) if tau is None else svalue(S,tau)
    return V-V0*math.exp(R*(T-(tau if tau is not None else 0.0)))
d0=sdelta(100.,T)
print(f"σ70 초기: 구조화 델타 {d0*100:.0f}% → 주식 편입 {d0*ALLOC*100:.1f}% · 순프리미엄 {-V0:+.2f}%/분기")

# ================= 1) MC 수익구조 scatter (3개월, 구조 100% 기준) =================
def mc_scatter():
    NP=10000; DAYS=63; dt=T/DAYS; rday=R/252
    drift=-0.5*SIG*SIG; vol=SIG*math.sqrt(dt)
    rng=np.random.default_rng(20260730)
    S=np.full(NP,100.0); V=np.ones(NP)
    def dvec(S,tau):
        sq=SIG*np.sqrt(tau); e=np.exp(-Q*tau)
        dp=e*(Nv((np.log(S/KP)+0.5*SIG*SIG*tau)/sq)-1)
        c1=e*Nv((np.log(S/K1)+0.5*SIG*SIG*tau)/sq)
        c2=e*Nv((np.log(S/K2)+0.5*SIG*SIG*tau)/sq)
        return np.clip(-dp+c1-c2,WMIN,WMAX)
    w=dvec(S,T); V*=1.0-TCB*w
    for st in range(1,DAYS+1):
        Sn=S*np.exp(drift*dt+vol*rng.standard_normal(NP))
        r0=Sn/S-1.0; S=Sn
        V*=1.0+w*r0+(1.0-w)*rday
        nw=dvec(S,max(T-st*dt,1e-8))
        V*=1.0-np.where(nw>w,TCB,TCS)*np.abs(nw-w); w=nw
    V*=1.0-TCS*w
    X=S; Y=(V-1)*100
    print(f"MC scatter: 평균 {Y.mean():+.1f}% · 중앙값 {np.median(Y):+.1f}% · 수익확률 {(Y>=0).mean()*100:.0f}%")
    fig,ax=plt.subplots(figsize=(9.6,6.0),dpi=140)
    m=(X>=50)&(X<=170)&(Y>=-45)&(Y<=40)
    ax.axhline(0,color='#8a97a8',lw=0.9); ax.axvline(100,color='#9aa7b8',ls='--',lw=1)
    ax.text(100,40,'S0=100',color=GRAY,fontsize=9,ha='center',va='top')
    ax.scatter(X[m],Y[m],s=3,color=NAVY,alpha=0.30,linewidths=0)
    B=40; ed=np.linspace(50,170,B+1); cen=(ed[:-1]+ed[1:])/2
    bm=np.full(B,np.nan)
    for b in range(B):
        sel=(X>=ed[b])&(X<ed[b+1])
        if sel.sum()>=5: bm[b]=np.clip(Y[sel].mean(),-45,40)
    ax.plot(cen,bm,color=ORANGE,lw=2.5,label='구간 평균')
    ax.set_xlim(50,170); ax.set_ylim(-45,40)
    ax.set_xticks(range(50,171,10))
    ax.set_xlabel('3개월(분기 만기) 기초자산 가격 (설정=100)',fontsize=10.5,color=NAVY)
    ax.set_ylabel('구조 수익률 (%)',fontsize=10.5,color=NAVY)
    ax.set_title('채권혼합 ETF 변동성 매매 파트 — 분기 수익 구조 (주식파트 100% 기준)',
                 fontsize=13,color=NAVY,fontweight='bold',loc='left')
    ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=10,frameon=False,loc='upper left')
    fig.tight_layout(); fig.savefig(os.path.join(IMG,'scat_bond3m.png'),bbox_inches='tight'); plt.close(fig)
    print("saved scat_bond3m.png")
mc_scatter()

# ================= 2) 편입비·예상수익률 테이블 PNG (0.5개월 단위) =================
LEVELS=[140,130,120,110,100,90,80,70,60]
TAUS=[('3.0',3/12),('2.5',2.5/12),('2.0',2/12),('1.5',1.5/12),('1.0',1/12),('0.5',0.5/12),('만기',None)]
def table_png(fname,title,fn,fmt,hl=None):
    fig,ax=plt.subplots(figsize=(7.4,3.6),dpi=150)
    ax.axis('off'); fig.patch.set_facecolor('white')
    ax.add_patch(plt.Rectangle((0.005,0.01),0.99,0.98,fill=False,ec='#d5dde6',lw=1.4,transform=ax.transAxes))
    ax.text(0.03,0.93,title,transform=ax.transAxes,fontsize=11,fontweight='bold',color=NAVY)
    cols=['지수/잔존']+[m+('개월' if m!='만기' else '') for m,_ in TAUS]
    xs=[0.03]+[0.16+i*0.12 for i in range(7)]
    for c,x in zip(cols,xs):
        ax.text(x,0.83,c,transform=ax.transAxes,fontsize=8.6,fontweight='bold',color=BLUE)
    ax.plot([0.02,0.97],[0.80,0.80],transform=ax.transAxes,color='#c9d5e2',lw=1.0)
    for i,lv in enumerate(LEVELS):
        y=0.74-i*0.075
        ax.text(xs[0],y,str(lv),transform=ax.transAxes,fontsize=8.4,fontweight='bold',color='#333')
        for j,(m,tau) in enumerate(TAUS):
            v=fn(float(lv),tau)
            c='#c05000' if (hl and hl(v)) else '#333333'
            ax.text(xs[j+1],y,fmt(v),transform=ax.transAxes,fontsize=8.4,color=c,
                    fontweight='bold' if lv==100 else 'normal')
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight',facecolor='white'); plt.close(fig)
    print("saved",fname)
table_png('tbl_bond_w.png','주식 편입비 (%)  — 구조화 델타 × 배분 50%',
          lambda lv,tau: sdelta(lv,(1/504 if tau is None else tau))*ALLOC*100, lambda v:f"{v:.0f}%")
table_png('tbl_bond_r.png','예상수익률 (원금 대비 %, 주식파트 50% + 채권 50% 연 2.5%)',
          lambda lv,tau: ALLOC*sret(lv,tau)+0.5*2.5*((T-(tau if tau is not None else 0))/1.0)*4*0.25,
          lambda v:f"{v:+.1f}%", hl=lambda v:v>=5.0)

# ================= 3) TOP2 실측: 분기 리셋 백테스트 =================
raw=pd.read_excel(XLS,sheet_name='삼성전자_하이닉스',header=None)
d=raw.iloc[14:]
s=pd.Series(pd.to_numeric(d.iloc[:,3],errors='coerce').values,index=pd.to_datetime(d.iloc[:,0]).values).dropna()
ii=pd.to_datetime(s.index); s=s[ii.dayofweek<5]
chg=s.pct_change().fillna(1.0); top2=s[chg!=0]
ret=top2.pct_change().dropna(); dts=ret.index
lr=np.log(1+ret)
vol60=(lr.rolling(60,min_periods=60).std()*math.sqrt(252)).bfill().clip(upper=SIGCAP)
rday=R/252

def run_bt(i0,i1):
    """분기(91일) 리셋 롤: 만기일 종가 청산(30bp)·같은 종가 재세팅(5bp)"""
    a=i0; V=1.0; navs=[]; ws=[]; dsl=[]; resets=[]
    S=100.; sig=max(float(vol60.iloc[a]),0.05)
    mat=dts[a]+pd.Timedelta(days=91)
    w=sdelta(100.,T,sig)*ALLOC
    V*=1.0-TCB*w
    dsl.append(dts[a]); navs.append(V); ws.append(w)
    for j in range(a+1,i1+1):
        r0=float(ret.iloc[j]); sig=max(float(vol60.iloc[j]),0.05)
        V*=1.0+w*r0+(1.0-w)*rday
        S*=1.0+r0
        if dts[j]>=mat and j<i1:              # 분기 만기: 리셋
            V*=1.0-TCS*w
            S=100.; mat=dts[j]+pd.Timedelta(days=91)
            nw=sdelta(100.,T,sig)*ALLOC
            V*=1.0-TCB*nw; w=nw; resets.append(dts[j])
        else:
            tau=max((mat-dts[j]).days/365.0,1e-8)
            nw=sdelta(S,tau,sig)*ALLOC
            V*=1.0-(TCB if nw>w else TCS)*abs(nw-w); w=nw
        dsl.append(dts[j]); navs.append(V); ws.append(w)
    return pd.DatetimeIndex(dsl),np.array(navs),np.array(ws),resets

i0=int(np.searchsorted(dts,pd.Timestamp('2021-07-28')))
dl,nav,wl,resets=run_bt(i0,len(dts)-1)
base=top2.loc[dl]/top2.loc[dl[0]]
bm=np.ones(len(dl))
for k in range(1,len(dl)):
    bm[k]=bm[k-1]*(1+0.4*float(base.iloc[k]/base.iloc[k-1]-1)+0.6*rday)
print(f"분기 리셋 백테스트 {dl[0].date()}~{dl[-1].date()}: 펀드 {nav[-1]*100-100:+.1f}% · BM {bm[-1]*100-100:+.1f}% · 기초 {float(base.iloc[-1])*100-100:+.1f}% · 리셋 {len(resets)}회")
fig,(ax1,ax2)=plt.subplots(2,1,figsize=(9.8,5.6),dpi=140,height_ratios=[1.7,1],sharex=True)
ax1.plot(dl,bm*100,color=GRAY,lw=1.7,ls='--',label='BM (TOP2 40% + 1년국고채, 매일 리밸)')
ax1.plot(dl,nav*100,color=ORANGE,lw=2.2,label='채권혼합 ETF (주식 50%·분기 리셋)')
for rd_ in resets: ax1.axvline(rd_,color='#e3c9a8',lw=0.7)
labs=sorted([(bm[-1]*100,GRAY),(nav[-1]*100,ORANGE)],key=lambda t:-t[0])
gap=(max(bm.max(),nav.max())*100-min(bm.min(),nav.min())*100)*0.055
pos=[]
for v,_ in labs: pos.append(v if not pos else min(v,pos[-1]-gap))
for (v,c),yy in zip(labs,pos):
    ax1.annotate(f"{v-100:+.1f}%",xy=(dl[-1],yy),xytext=(4,0),textcoords='offset points',color=c,fontsize=10,fontweight='bold',va='center')
ax1.set_xlim(dl[0],dl[-1]+pd.Timedelta(days=45))
ax1.set_title(f'TOP2 실측 백테스트 ({dl[0].date()} ~ {dl[-1].date()}) — 분기 행사가 리셋 · σ 상한 70%',
              fontsize=12.5,color=NAVY,fontweight='bold',loc='left')
ax1.axhline(100,color='#c9d5e2',lw=0.8)
ax1.legend(fontsize=9,frameon=False,loc='upper left')
ax1.grid(alpha=0.22); ax1.spines[['top','right']].set_visible(False)
ax2.fill_between(dl,wl*100,color=ORANGE,alpha=0.35,lw=0)
ax2.axhline(50,color='#c05000',ls=':',lw=1.0)
ax2.set_ylim(0,55); ax2.set_ylabel('주식 편입비(%)',fontsize=9,color=NAVY)
ax2.grid(alpha=0.2); ax2.spines[['top','right']].set_visible(False)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
fig.text(0.99,0.01,'세로선=분기 리셋 · 점선=주식 상한 50% · 매수 5bp/매도 30bp · 채권·현금 연 2.5% 가정 · 데이터: 기준 엑셀',ha='right',color=GRAY,fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG,'bt_bond_full.png'),bbox_inches='tight'); plt.close(fig)
print("saved bt_bond_full.png")

# 분기별 요약 테이블
qs=[dl[0]]+resets+[dl[-1]]
rows=[]
navS=pd.Series(nav,index=dl); baseS=pd.Series(base.values,index=dl)
for k in range(len(qs)-1):
    a,b=qs[k],qs[k+1]
    rows.append((f"{a.strftime('%y.%m.%d')}~{b.strftime('%y.%m.%d')}",
                 float(baseS[b]/baseS[a]-1)*100, float(navS[b]/navS[a]-1)*100))
fig,ax=plt.subplots(figsize=(7.6,3.35),dpi=150)   # 슬롯(4.98×2.03in) 비율
ax.axis('off'); fig.patch.set_facecolor('white')
ax.add_patch(plt.Rectangle((0.005,0.005),0.99,0.99,fill=False,ec='#d5dde6',lw=1.4,transform=ax.transAxes))
ax.text(0.03,0.93,'분기(리셋 단위) 성과 요약',transform=ax.transAxes,fontsize=11,fontweight='bold',color=NAVY)
half=(len(rows)+1)//2
for blk,(x0,rws) in enumerate((( 0.03,rows[:half]),(0.53,rows[half:]))):
    for c,x in (('기간',x0),('기초',x0+0.27),('펀드',x0+0.38)):
        ax.text(x,0.83,c,transform=ax.transAxes,fontsize=8.0,fontweight='bold',color=BLUE)
    ax.plot([x0,x0+0.44],[0.80,0.80],transform=ax.transAxes,color='#c9d5e2',lw=0.9)
    for i,(p,b_,f_) in enumerate(rws):
        y=0.755-i*0.062
        ax.text(x0,y,p,transform=ax.transAxes,fontsize=6.9,color='#333')
        ax.text(x0+0.27,y,f"{b_:+.0f}%",transform=ax.transAxes,fontsize=7.2,color='#333',ha='left')
        ax.text(x0+0.38,y,f"{f_:+.1f}%",transform=ax.transAxes,fontsize=7.2,color=NAVY,fontweight='bold',ha='left')
fig.savefig(os.path.join(IMG,'bt_bond_table.png'),bbox_inches='tight',facecolor='white'); plt.close(fig)
print(f"saved bt_bond_table.png ({len(rows)}분기)")

# ================= 4) 최근 3개월 실측 (4/28 앵커) =================
i3=int(np.searchsorted(dts,pd.Timestamp('2026-04-29')))
d3,n3,w3,r3=run_bt(i3-1,len(dts)-1)
b3=top2.loc[d3]/top2.loc[d3[0]]
bm3=np.ones(len(d3))
for k in range(1,len(d3)):
    bm3[k]=bm3[k-1]*(1+0.4*float(b3.iloc[k]/b3.iloc[k-1]-1)+0.6*rday)
print(f"3개월 실측: 펀드 {n3[-1]*100-100:+.1f}% · BM {bm3[-1]*100-100:+.1f}% · 기초 {float(b3.iloc[-1])*100-100:+.1f}%")
fig,(ax1,ax2)=plt.subplots(2,1,figsize=(9.8,5.4),dpi=140,height_ratios=[1.6,1],sharex=True)
ax1.plot(d3,bm3*100,color=GRAY,lw=1.7,ls='--',label='BM (TOP2 40% + 1년국고채, 매일 리밸)')
ax1.plot(d3,n3*100,color=ORANGE,lw=2.2,label='채권혼합 ETF')
labs=sorted([(bm3[-1]*100,GRAY),(n3[-1]*100,ORANGE)],key=lambda t:-t[0])
gap=(max(bm3.max(),n3.max())*100-min(bm3.min(),n3.min())*100)*0.075
pos=[]
for v,_ in labs: pos.append(v if not pos else min(v,pos[-1]-gap))
for (v,c),yy in zip(labs,pos):
    ax1.annotate(f"{v-100:+.1f}%",xy=(d3[-1],yy),xytext=(4,0),textcoords='offset points',color=c,fontsize=10,fontweight='bold',va='center')
for rd_ in r3: ax1.axvline(rd_,color='#c05000',ls=':',lw=1.0)
ax1.set_xlim(d3[0],d3[-1]+pd.Timedelta(days=6))
ax1.axhline(100,color='#c9d5e2',lw=0.8)
ax1.set_title('최근 3개월 실측 (기준가 2026-04-28 종가 ~ 07-28) — 기초 +48% 급등 후 -5% 왕복 구간',
              fontsize=12,color=NAVY,fontweight='bold',loc='left')
ax1.legend(fontsize=9,frameon=False,loc='upper left')
ax1.grid(alpha=0.22); ax1.spines[['top','right']].set_visible(False)
off=pd.Timedelta(hours=10)
ax2.bar(d3,w3*100,width=0.65,color=ORANGE,alpha=0.85)
ax2.axhline(50,color='#c05000',ls=':',lw=1.0)
ax2.set_ylim(0,55); ax2.set_ylabel('주식 편입비(%)',fontsize=9,color=NAVY)
ax2.grid(alpha=0.2,axis='y'); ax2.spines[['top','right']].set_visible(False)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
fig.text(0.99,0.01,'점선(수직)=분기 리셋 · σ=직전 60영업일 연환산(상한 70%) · 주식 배분 50% · 매수 5bp/매도 30bp',ha='right',color=GRAY,fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG,'bt_bond_3m.png'),bbox_inches='tight'); plt.close(fig)
print("saved bt_bond_3m.png")

# ================= 5) 구간별 예시: 상승 추세 / 변동장 / 하락장 (신규 설정, BM vs 펀드) =================
WINDOWS=[('하락장 1년','2021-12-30',365,'채권 50% + 저가매수로 방어','bt_bond_down.png'),
         ('변동장 1년','2024-07-25',365,'등락 반복을 매매로 수확 → BM 초과','bt_bond_flat.png'),
         ('상승 추세 1년','2025-06-02',365,'이익을 확정하며 상승에 참여','bt_bond_up.png')]
for nm,t0,ndays,msg,fname in WINDOWS:
    i0w=int(np.searchsorted(dts,pd.Timestamp(t0)))
    dw,nw_,ww,rw=run_bt(i0w,int(np.searchsorted(dts,dts[i0w]+pd.Timedelta(days=ndays),side='right'))-1)
    bmw=np.ones(len(dw)); bw=top2.loc[dw]/top2.loc[dw[0]]
    for k in range(1,len(dw)):
        bmw[k]=bmw[k-1]*(1+0.4*float(bw.iloc[k]/bw.iloc[k-1]-1)+0.6*rday)
    fig,ax=plt.subplots(figsize=(5.4,4.15),dpi=150)
    ax.plot(dw,bmw*100,color=GRAY,lw=1.8,ls='--',label='BM')
    ax.plot(dw,nw_*100,color=ORANGE,lw=2.4,label='채권혼합 ETF')
    ax.axhline(100,color='#c9d5e2',lw=0.8)
    for rd_ in rw: ax.axvline(rd_,color='#e3c9a8',lw=0.7)
    f1=nw_[-1]*100-100; b1=bmw[-1]*100-100
    ttl=f"{nm} ({dw[0].strftime('%y.%m')}~{dw[-1].strftime('%y.%m')})"+chr(10)+f"펀드 {f1:+.1f}% vs BM {b1:+.1f}%"
    ax.set_title(ttl,fontsize=12.5,color=NAVY,fontweight='bold',loc='left')
    ax.text(0.02,0.02,msg,transform=ax.transAxes,fontsize=10.5,color='#c05000',fontweight='bold',va='bottom')
    ax.legend(fontsize=9.5,frameon=False,loc='best')
    ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
    ax.tick_params(labelsize=8.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
    fig.tight_layout(pad=0.5)
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print(f"saved {fname}: 펀드 {f1:+.1f}% vs BM {b1:+.1f}%")
print("done")
