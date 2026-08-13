# -*- coding: utf-8 -*-
"""IT TOP10 스마트 액티브 레버리지 1.5 — 제안서 자산 생성
- 기초: TIGER 반도체TOP10 NAV (A396500, ETF_데이터_pivot) · BM = 기초 일간수익률 ×1.5 (매일 리밸)
- 전략(백테스트용, 제안서엔 구체 수치 미기재 — 액티브 표방):
  기준 편입비 150% · 직전 리밸 기준 지수 ±5% 이상 변동 시에만 조정
  조정폭 = 변동 1%당 2%p 반대 방향 (상승→축소, 하락→확대) · 편입비 범위 [100%, 200%]
- 회계: V ×= 1 + w×r + (1-w)×rday (w>1이면 차입비용 자동 반영, 연 2.5%) · 매수 5bp/매도 30bp
"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#8fa8bf'; RED='#C0392B'; BLUE='#2E5F97'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
PARQ="C:/Users/gamer38/Documents/Claude/Projects/ETF WEB/ETF_데이터_pivot.parquet"

R=0.025; rday=R/252; TCB,TCS=0.0005,0.0030
W0=1.50; STEP=2.0; TRIG=0.05; WLO,WHI=1.00,2.00

df=pd.read_parquet(PARQ)
def nav_series(code):
    k=df[df['종목코드']==code].dropna(subset=['ETF순자산가치(NAV)(원)']).sort_values('날짜')
    s=pd.Series(k['ETF순자산가치(NAV)(원)'].astype(float).values,index=pd.to_datetime(k['날짜']).values)
    i=pd.to_datetime(s.index); s=s[i.dayofweek<5]
    chg=s.pct_change().fillna(1.0); return s[chg!=0]
base=nav_series('A396500')          # TIGER 반도체TOP10
lev2=nav_series('A488080')          # TIGER 반도체TOP10레버리지 (2배, 실측 잠식 사례용)
ret=base.pct_change().dropna(); dts=ret.index
print(f"기초(TIGER 반도체TOP10 NAV): {dts[0].date()} ~ {dts[-1].date()} ({len(ret)}영업일)")

def run_smart(i0,i1):
    """스마트 액티브 1.5 (대표 규칙: 매매 최소화 밴드)
    - 노출을 방치해 상승 시 레버리지율이 자연 하락(=상대 축소), 하락 시 상승(=확대)
    - 레버리지율이 [1.35, 1.65] 밴드를 벗어날 때만 1.5로 복원 (큰 변동에만 매매)"""
    LO,HI=1.35,1.65
    V=1.0; E=1.5; ntr=0
    V*=1.0-TCB*1.5
    dl=[dts[i0]]; nf=[V]; nb=[1.0]; ws=[1.5]; bm=1.0
    for j in range(i0+1,i1+1):
        r0=float(ret.iloc[j])
        L=E/V
        V*=1.0+L*r0+(1.0-L)*rday
        E*=1.0+r0
        bm*=1.0+1.5*r0-0.5*rday
        L=E/V
        if L<LO or L>HI:
            tgt=1.5*V; dtr=abs(tgt-E)/V
            V*=1.0-(TCB if tgt>E else TCS)*dtr
            E=1.5*V; L=1.5; ntr+=1
        dl.append(dts[j]); nf.append(V); nb.append(bm); ws.append(L)
    return pd.DatetimeIndex(dl),np.array(nf),np.array(nb),np.array(ws),ntr

i0=0; i1=len(dts)-1
dl,nf,nb,ws,ntr=run_smart(i0,i1)
def stats(nm,arr,dl):
    yrs=(dl[-1]-dl[0]).days/365.25
    dr=pd.Series(arr).pct_change().dropna()
    mdd=(pd.Series(arr)/pd.Series(arr).cummax()-1).min()
    print(f"[{nm}] 누적 {arr[-1]*100-100:+7.1f}% · 연환산 {(arr[-1]**(1/yrs)-1)*100:+5.1f}% · 변동성 {dr.std()*math.sqrt(252)*100:4.1f}% · MDD {mdd*100:5.1f}%")
    return mdd
b0=base/base.iloc[0]
print(f"기초 누적 {float(b0.iloc[-1])*100-100:+.1f}%")
mddF=stats('스마트 1.5',nf,dl); mddB=stats('BM(1.5배 매일)',nb,dl)
print(f"리밸 {ntr}회 (BM은 매일 {len(dl)-1}회) · 평균 레버리지율 {ws.mean():.2f}배")

# ---- 차트 1: 전체 백테스트 (NAV + 드로우다운) ----
fig,(ax1,ax2)=plt.subplots(2,1,figsize=(9.8,5.8),dpi=140,height_ratios=[1.7,1],sharex=True)
ax1.plot(dl,nb*100,color=GRAY,lw=1.7,label=f'BM (기초 1.5배 매일 재조정)')
ax1.plot(dl,nf*100,color=ORANGE,lw=2.2,label='IT TOP10 스마트 액티브 레버리지 1.5 (시뮬)')
ax1.axhline(100,color='#c9d5e2',lw=0.8)
labs=sorted([(nb[-1]*100,GRAY),(nf[-1]*100,ORANGE)],key=lambda t:-t[0])
gap=(max(nb.max(),nf.max())-min(nb.min(),nf.min()))*100*0.055
pos=[]
for v,_ in labs: pos.append(v if not pos else min(v,pos[-1]-gap))
for (v,c),yy in zip(labs,pos):
    ax1.annotate(f"{v-100:+.0f}%",xy=(dl[-1],yy),xytext=(4,0),textcoords='offset points',color=c,fontsize=10,fontweight='bold',va='center')
ax1.set_xlim(dl[0],dl[-1]+pd.Timedelta(days=60))
ax1.set_title(f'실측 백테스트 ({dl[0].date()} ~ {dl[-1].date()}) — 기초: TIGER 반도체TOP10 NAV',
              fontsize=12.5,color=NAVY,fontweight='bold',loc='left')
ax1.legend(fontsize=9,frameon=False,loc='upper left')
ax1.grid(alpha=0.22); ax1.spines[['top','right']].set_visible(False)
ddF=(pd.Series(nf,index=dl)/pd.Series(nf,index=dl).cummax()-1)*100
ddB=(pd.Series(nb,index=dl)/pd.Series(nb,index=dl).cummax()-1)*100
ax2.fill_between(dl,ddB.values,color=GRAY,alpha=0.30,lw=0)
ax2.plot(dl,ddB.values,color=GRAY,lw=1.1,label=f'BM 드로우다운 (최대 {ddB.min():.0f}%)')
ax2.fill_between(dl,ddF.values,color=ORANGE,alpha=0.40,lw=0)
ax2.plot(dl,ddF.values,color=ORANGE,lw=1.3,label=f'펀드 드로우다운 (최대 {ddF.min():.0f}%)')
ax2.set_ylabel('고점 대비 낙폭(%)',fontsize=9,color=NAVY)
ax2.legend(fontsize=8.3,frameon=False,loc='lower left')
ax2.grid(alpha=0.2); ax2.spines[['top','right']].set_visible(False)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
fig.text(0.99,0.01,'평균 1.5배 추종 · 상승 시 축소/하락 시 확대 · 큰 변동에만 재조정 · 매수 5bp/매도 30bp·차입 연 2.5% 반영 · 데이터: ETF데이터(NAV)',
         ha='right',color=GRAY,fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG,'lev15_full.png'),bbox_inches='tight'); plt.close(fig)
print("saved lev15_full.png")

# ---- 차트 2: 편입비 추이 ----
fig,ax=plt.subplots(figsize=(9.8,3.0),dpi=140)
ax.plot(dl,ws*100,color=ORANGE,lw=1.3)
ax.fill_between(dl,135,np.clip(ws*100,135,165),color=ORANGE,alpha=0.12)
ax.axhline(150,color='#c05000',ls=':',lw=1.2); ax.axhline(135,color='#c9d5e2',lw=0.9); ax.axhline(165,color='#c9d5e2',lw=0.9)
ax.text(dl[3],151.5,'기준 1.5배',color='#c05000',fontsize=9.5,fontweight='bold')
b2=b0/b0.iloc[0]
ax2=ax.twinx()
ax2.plot(b0.index,b0.values*100,color=SKY,lw=1.2,alpha=0.9)
ax2.set_ylabel('기초지수(시작=100, 로그)',fontsize=9,color=GRAY)
ax2.set_yscale('log')
ax.set_ylim(125,175); ax.set_ylabel('레버리지율(%)',fontsize=10,color=NAVY)
ax.set_title('레버리지율 추이 — 오르면 자연히 줄고, 내리면 늘어난다 · 밴드 이탈 시에만 재조정 (시뮬)',fontsize=12,color=NAVY,fontweight='bold',loc='left')
ax.grid(alpha=0.2); ax.spines[['top']].set_visible(False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
fig.tight_layout()
fig.savefig(os.path.join(IMG,'lev15_weight.png'),bbox_inches='tight'); plt.close(fig)
print("saved lev15_weight.png")

# ---- 차트 3: 변동성 잠식 실측 (기초 vs 2배 레버리지 ETF NAV) ----
lb=lev2/lev2.iloc[0]
bb_=base.loc[base.index>=lev2.index[0]]; bb_=bb_/bb_.iloc[0]
fig,ax=plt.subplots(figsize=(9.6,4.4),dpi=140)
ax.plot(bb_.index,(bb_.values-1)*100,color=NAVY,lw=2.0,label='TIGER 반도체TOP10 (기초, NAV)')
ax.plot(lb.index,(lb.values-1)*100,color=RED,lw=2.0,label='TIGER 반도체TOP10레버리지 (2배, NAV)')
simple2=(bb_.values-1)*2*100
ax.plot(bb_.index,simple2,color=GRAY,lw=1.4,ls='--',label='단순 2배 (기초×2)')
ax.axhline(0,color='#9db4cc',lw=0.9)
f_lev=(float(lb.iloc[-1])-1)*100; f_b2=simple2[-1]
ax.annotate(f"{f_lev:+.0f}%",xy=(lb.index[-1],f_lev),xytext=(5,0),textcoords='offset points',color=RED,fontsize=11,fontweight='bold',va='center')
ax.annotate(f"{f_b2:+.0f}%",xy=(bb_.index[-1],f_b2),xytext=(5,0),textcoords='offset points',color=GRAY,fontsize=11,fontweight='bold',va='center')
ax.set_title(f'변동성 잠식 실측 — 레버리지 ETF는 단순 2배보다 {f_b2-f_lev:.0f}%p 덜 벌었다 (상장 후 전체)',
             fontsize=12.5,color=NAVY,fontweight='bold',loc='left')
ax.set_ylabel('누적 수익률(%)',fontsize=10,color=NAVY)
ax.legend(fontsize=9.5,frameon=False,loc='upper left')
ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
fig.text(0.99,0.01,f'기간 {lb.index[0].date()}~{lb.index[-1].date()} · NAV 기준 · 데이터: ETF데이터',ha='right',color=GRAY,fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG,'lev15_decay.png'),bbox_inches='tight'); plt.close(fig)
print(f"saved lev15_decay.png (레버리지 {f_lev:+.0f}% vs 단순2배 {f_b2:+.0f}%)")

# ---- 차트 4: 일일 재조정 물량 추정 ----
k=df[df['종목코드']=='A488080'].dropna(subset=['순자산총액(백만원)']).sort_values('날짜')
aum=pd.Series(k['순자산총액(백만원)'].astype(float).values/100,index=pd.to_datetime(k['날짜']).values)  # 억원
i=pd.to_datetime(aum.index); aum=aum[i.dayofweek<5]
r2=lev2.pct_change().reindex(aum.index)
under=base.pct_change().reindex(aum.index)
rebal=(aum*2*under.abs()).dropna()   # 재조정 물량 ≈ AUM×2×|기초 일수익률|
fig,ax=plt.subplots(figsize=(9.6,4.2),dpi=140)
ax.bar(rebal.index,rebal.values,width=1.4,color=RED,alpha=0.75)
top=rebal.max()
ax.set_title(f'레버리지 ETF 일일 재조정 매매 추정 물량 — 최대 {top:,.0f}억원이 장 마감 직전에 쏠린다',
             fontsize=12.5,color=NAVY,fontweight='bold',loc='left')
ax.set_ylabel('추정 재조정 매매(억원)',fontsize=10,color=NAVY)
ax.grid(alpha=0.22,axis='y'); ax.spines[['top','right']].set_visible(False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
fig.text(0.99,0.01,'추정 = 순자산총액×2×|기초 일수익률| (TIGER 반도체TOP10레버리지) · 실제 체결과 다를 수 있음 · 데이터: ETF데이터',
         ha='right',color=GRAY,fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(IMG,'lev15_rebalflow.png'),bbox_inches='tight'); plt.close(fig)
print(f"saved lev15_rebalflow.png (최대 {top:,.0f}억)")

# ---- 차트 5: 국면별 (하락/횡보/급등/최근급락) — 신규 설정 ----
def run_win(t0,t1,fname,title,msg):
    a=int(np.searchsorted(dts,pd.Timestamp(t0)))
    b=int(np.searchsorted(dts,pd.Timestamp(t1),side='right'))-1
    dw,f_,b_,w_,_=run_smart(a,b)
    fig,ax=plt.subplots(figsize=(5.4,4.15),dpi=150)
    ax.plot(dw,b_*100,color=GRAY,lw=1.9,label='BM (1.5배 매일)')
    ax.plot(dw,f_*100,color=ORANGE,lw=2.4,label='스마트 1.5 (시뮬)')
    ax.axhline(100,color='#c9d5e2',lw=0.8)
    f1=f_[-1]*100-100; b1=b_[-1]*100-100
    ttl=f"{title} ({dw[0].strftime('%y.%m')}~{dw[-1].strftime('%y.%m')})"+chr(10)+f"펀드 {f1:+.1f}% vs BM {b1:+.1f}%"
    ax.set_title(ttl,fontsize=12.5,color=NAVY,fontweight='bold',loc='left')
    ax.text(0.02,0.02,msg,transform=ax.transAxes,fontsize=10.5,color='#c05000',fontweight='bold',va='bottom')
    ax.legend(fontsize=9.5,frameon=False,loc='best')
    ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
    ax.tick_params(labelsize=8.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
    fig.tight_layout(pad=0.5)
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print(f"saved {fname}: 펀드 {f1:+.1f}% vs BM {b1:+.1f}%")
run_win('2024-07-11','2025-04-30','lev15_down.png','하락 후 회복(왕복) 구간','재조정을 멈춰 왕복 비용을 회피')
run_win('2021-08-10','2022-12-30','lev15_flat.png','하락장 (21.08~22.12)','하락 구간에도 BM과 대등하게 방어')
run_win('2025-06-02','2026-06-02','lev15_up.png','급등 구간','이익을 확정하며 1.5배 상승 참여')
run_win('2026-06-22','2026-08-12','lev15_crash.png','최근 급락 (26.6~8)','하락 시 확대 — 반등 탄력 확보')
print("done")
