# -*- coding: utf-8 -*-
"""P5·P6 차트 v2
- P5 3분할: ① KOSPI200 4년5개월 왕복 ② 하이닉스레버리지 출시가 복귀(05.27~07.03) ③ 왕복 창(06.05~07.08)
- P6 (ETF웹 '레버리지 ETF' 레슨, 책 3-1 참조): 산술 극단(기존 lev15_arith0 유지) +
  ② 제자리 실측(2026.02.26~04.16, K200 -0.3% vs 레버리지 -9.1%, 한때 -41%) ③ 추세장(03.31~05.29, +79.5%→실제 +207%)
데이터: ETF_데이터_pivot
"""
import os, platform, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#8fa8bf'; RED='#C0392B'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
df=pd.read_parquet("C:/Users/gamer38/Documents/Claude/Projects/ETF WEB/ETF_데이터_pivot.parquet")

def px(nm,col='수정주가(원)'):
    k=df[df['종목명']==nm].dropna(subset=[col]).sort_values('날짜')
    s=pd.Series(k[col].astype(float).values,index=pd.to_datetime(k['날짜']).values)
    i=pd.to_datetime(s.index); s=s[i.dayofweek<5]
    chg=s.pct_change().fillna(1.0); return s[chg!=0]
k1=px('KODEX 200'); k2=px('KODEX 레버리지')
hv=px('KODEX SK하이닉스단일종목레버리지')
# SK하이닉스 실제 수정주가 (data 폴더, DataGuide, ~2026-08-14)
_d=pd.read_excel(os.path.join(BASE,'..','data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx'),
                 sheet_name=0,header=None,skiprows=14)
hx=pd.Series(_d[2].astype(float).values,index=pd.to_datetime(_d[0])).sort_index().dropna()

def style(ax):
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    ax.grid(axis='y',color='#e6ebf1',lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(labelsize=8.5)
FS=(3.85,3.5)

# ---------- P5-① KOSPI200 4년5개월 왕복 (소형) ----------
t0,t1=pd.Timestamp('2020-12-30'),pd.Timestamp('2025-05-28')
w1=k1[(k1.index>=t0)&(k1.index<=t1)]; w2=k2[(k2.index>=t0)&(k2.index<=t1)]
r1=w1/w1.iloc[0]*100; r2=w2/w2.iloc[0]*100
print(f"[P5-①] 기초 {r1.iloc[-1]-100:+.1f}% · 레버리지 {r2.iloc[-1]-100:+.1f}%")
fig,ax=plt.subplots(figsize=FS,dpi=150)
ax.plot(r1.index,r1.values,color=NAVY,lw=1.5,label='KOSPI200')
ax.plot(r2.index,r2.values,color=RED,lw=1.5,label='KODEX 레버리지')
ax.axhline(100,color='#b8c6d4',lw=0.9,ls='--')
ax.annotate(f"지수 {r1.iloc[-1]-100:+.1f}% (제자리)",xy=(pd.Timestamp('2023-04-01'),114),
            fontsize=9.5,fontweight='bold',color=NAVY,ha='left')
ax.annotate(f"레버리지 {r2.iloc[-1]-100:+.1f}%",xy=(pd.Timestamp('2023-04-01'),44),
            fontsize=9.5,fontweight='bold',color=RED,ha='left')
ax.set_ylim(38,127)
ax.set_title("① KOSPI200 왕복 4년 5개월\n(2020.12.30 → 2025.05.28)",fontsize=10,fontweight='bold',color='#222')
ax.legend(fontsize=7.5,loc='lower left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
ax.xaxis.set_major_locator(mdates.YearLocator()); style(ax)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_long_k200.png')); plt.close()

# ---------- P5-② 출시 → 주가 보합 시점(07.07) : 주가·레버리지 모두 실제값 ----------
a,b=pd.Timestamp('2026-05-27'),pd.Timestamp('2026-07-07')
h=hv[(hv.index>=a)&(hv.index<=b)]
s=hx[(hx.index>=a)&(hx.index<=b)]
rl=h/h.iloc[0]*100; rs=s/s.iloc[0]*100
gl=float(rl.iloc[-1])-100; gs=float(rs.iloc[-1])-100
print(f"[P5-②] {a.date()}~{b.date()}: 주가 실제 {gs:+.1f}% · 레버리지 실제 {gl:+.1f}% ({h.iloc[0]:,.0f}→{h.iloc[-1]:,.0f}원)")
fig,ax=plt.subplots(figsize=FS,dpi=150)
ax.plot(rs.index,rs.values,color=NAVY,lw=1.6,label='SK하이닉스 주가 (실제)')
ax.plot(rl.index,rl.values,color=RED,lw=1.7,label='KODEX 하이닉스 레버리지 (실제)')
ax.axhline(100,color='#b8c6d4',lw=0.9,ls='--')
ax.annotate(f"주가\n{gs:+.1f}%\n(보합)",xy=(rs.index[-1],rs.iloc[-1]),xytext=(6,-4),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color=NAVY)
ax.annotate(f"레버리지\n{gl:+.1f}%",xy=(rl.index[-1],rl.iloc[-1]),xytext=(6,-20),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color=RED)
ax.scatter([rl.index[-1]],[rl.iloc[-1]],s=32,color=RED,zorder=5)
ax.set_title("② 하이닉스 레버리지 : 상장 6주\n(2026.05.27 상장 → 07.07)",fontsize=10,fontweight='bold',color='#222')
ax.legend(fontsize=7.5,loc='upper left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7)); style(ax)
ax.set_xlim(rl.index[0]-pd.Timedelta(days=2),rl.index[-1]+pd.Timedelta(days=12))
ax.set_ylim(min(rl.min(),rs.min())-8,max(rl.max(),rs.max())+8)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_hynix_a.png')); plt.close()

# ---------- P5-③ 왕복 창 06.05~07.08 : 주가·레버리지 모두 실제값 ----------
a,b=pd.Timestamp('2026-06-05'),pd.Timestamp('2026-07-08')
h=hv[(hv.index>=a)&(hv.index<=b)]
s=hx[(hx.index>=a)&(hx.index<=b)]
rl=h/h.iloc[0]*100; rs=s/s.iloc[0]*100
gl=float(rl.iloc[-1])-100; gs=float(rs.iloc[-1])-100
print(f"[P5-③] {a.date()}~{b.date()}: 주가 실제 {gs:+.1f}% · 레버리지 실제 {gl:+.1f}% ({h.iloc[0]:,.0f}→{h.iloc[-1]:,.0f}원)")
fig,ax=plt.subplots(figsize=FS,dpi=150)
ax.plot(rs.index,rs.values,color=NAVY,lw=1.6,label='SK하이닉스 주가 (실제)')
ax.plot(rl.index,rl.values,color=RED,lw=1.7,label='KODEX 하이닉스 레버리지 (실제)')
ax.axhline(100,color='#b8c6d4',lw=0.9,ls='--')
ax.annotate(f"주가\n{gs:+.1f}%\n(제자리)",xy=(rs.index[-1],rs.iloc[-1]),xytext=(6,-4),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color=NAVY)
ax.annotate(f"레버리지\n{gl:+.1f}%",xy=(rl.index[-1],rl.iloc[-1]),xytext=(6,-20),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color=RED)
ax.scatter([rl.index[-1]],[rl.iloc[-1]],s=32,color=RED,zorder=5)
ax.set_title("③ 하이닉스 레버리지 : 왕복 5주\n(2026.06.05 → 07.08)",fontsize=10,fontweight='bold',color='#222')
ax.legend(fontsize=7.5,loc='upper left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7)); style(ax)
ax.set_xlim(rl.index[0]-pd.Timedelta(days=2),rl.index[-1]+pd.Timedelta(days=10))
ax.set_ylim(min(rl.min(),rs.min())-18,max(rl.max(),rs.max())+8)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_hynix_b.png')); plt.close()

# ---------- P6-① 극단 예시 (책 그림 3-1.1) : 시장 2배 → 제자리 = 레버리지 0원 ----------
fig,ax=plt.subplots(figsize=FS,dpi=150)
xs=[0,1,2]
ax.plot(xs,[100,200,100],color=NAVY,lw=2.2,marker='o',ms=6,label='지수')
ax.plot(xs,[100,300,0],color=RED,lw=2.2,marker='o',ms=6,label='레버리지 2배')
for x,y,t,c,dy in [(1,200,'+100%',NAVY,10),(2,100,'-50%  (제자리)',NAVY,10),
                   (1,300,'+200%',RED,10),(2,0,'-100% → 0원',RED,12)]:
    ax.annotate(t,xy=(x,y),xytext=(0,dy),textcoords='offset points',ha='center',
                fontsize=10,fontweight='bold',color=c)
ax.set_xticks(xs); ax.set_xticklabels(['시작','시장 2배 상승','시장 제자리'],fontsize=9.5)
ax.set_ylim(-40,345); style(ax)
ax.set_title("극단 예시 : 시장이 2배 갔다가\n제자리로 오면, 레버리지는 0원",fontsize=10,fontweight='bold',color='#222')
ax.legend(fontsize=8.5,loc='upper left',frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_arith0.png')); plt.close()

# ---------- P6-② 제자리 실측 2026.02.26~04.16 ----------
a,b=pd.Timestamp('2026-02-26'),pd.Timestamp('2026-04-16')
w1=k1[(k1.index>=a)&(k1.index<=b)]; w2=k2[(k2.index>=a)&(k2.index<=b)]
r1=w1/w1.iloc[0]*100; r2=w2/w2.iloc[0]*100
tmin=r2.idxmin()
print(f"[P6-②] {a.date()}~{b.date()}: K200 {r1.iloc[-1]-100:+.1f}% · 레버리지 {r2.iloc[-1]-100:+.1f}% · 최저 {r2.min()-100:+.1f}% ({tmin.date()})")
fig,ax=plt.subplots(figsize=FS,dpi=150)
ax.plot(r1.index,r1.values,color=NAVY,lw=1.6,label='KOSPI200')
ax.plot(r2.index,r2.values,color=RED,lw=1.6,label='KODEX 레버리지')
ax.axhline(100,color='#b8c6d4',lw=0.9,ls='--')
ax.annotate(f"지수 {r1.iloc[-1]-100:+.1f}%\n(제자리)",xy=(r1.index[-1],r1.iloc[-1]),xytext=(-56,10),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color=NAVY)
ax.annotate(f"레버리지\n{r2.iloc[-1]-100:+.1f}%",xy=(r2.index[-1],r2.iloc[-1]),xytext=(-50,-34),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color=RED)
ax.annotate(f"한때 {r2.min()-100:+.1f}%",xy=(tmin,r2.min()),xytext=(-14,-16),
            textcoords='offset points',fontsize=9,fontweight='bold',color=RED,
            arrowprops=dict(arrowstyle='-',color=RED,lw=0.8))
ax.set_title("실측 : 지수 제자리 7주\n(2026.02.26 ~ 04.16)",fontsize=10,fontweight='bold',color='#222')
ax.legend(fontsize=7.5,loc='upper left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%d')); style(ax)
ax.set_ylim(r2.min()-14,max(r1.max(),r2.max())+8)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_k200flat.png')); plt.close()

# ---------- P6-③ 추세장 2026.03.31~05.29 ----------
a,b=pd.Timestamp('2026-03-31'),pd.Timestamp('2026-05-29')
w1=k1[(k1.index>=a)&(k1.index<=b)]; w2=k2[(k2.index>=a)&(k2.index<=b)]
rb=w1/w1.iloc[0]; rl=w2/w2.iloc[0]
simple=1.0+(rb-1.0)*2.0
print(f"[P6-③] {a.date()}~{b.date()}: K200 {float(rb.iloc[-1])*100-100:+.1f}% · 단순2배 {float(simple.iloc[-1])*100-100:+.1f}% · 실제 {float(rl.iloc[-1])*100-100:+.1f}%")
fig,ax=plt.subplots(figsize=FS,dpi=150)
ax.plot(rl.index,rl.values*100,color=ORANGE,lw=1.9,label='레버리지 실제 (복리)')
ax.plot(simple.index,simple.values*100,color=GRAY,lw=1.5,ls='--',label='단순 2배 (가상)')
ax.plot(rb.index,rb.values*100,color=NAVY,lw=1.4,label='KOSPI200')
for sr,c,dy in [(rl,ORANGE,2),(simple,GRAY,4),(rb,NAVY,2)]:
    ax.annotate(f"{float(sr.iloc[-1])*100-100:+.0f}%",xy=(sr.index[-1],sr.iloc[-1]*100),xytext=(-38,dy),
                textcoords='offset points',fontsize=9.5,fontweight='bold',color=c)
ax.annotate("복리 효과\n+48%p",xy=(rl.index[-9],float(rl.iloc[-9])*100),xytext=(-72,6),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color='#b45309')
ax.set_title("단, 추세장에선 복리가 유리\n(2026.03.31 ~ 05.29)",fontsize=10,fontweight='bold',color='#222')
ax.legend(fontsize=7.5,loc='upper left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%d')); style(ax)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_k200trend.png')); plt.close()
print("저장: lev15_long_k200, lev15_hynix_a, lev15_hynix_b, lev15_k200flat, lev15_k200trend")
