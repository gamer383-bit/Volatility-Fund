# -*- coding: utf-8 -*-
"""스마트 레버리지 덱 P5-7 재작업용 실측 차트 6종
- P5: 긴 구간 변동성 잠식 (KOSPI200 4년5개월 왕복 / 하이닉스레버리지 출시가 복귀·왕복 창)
- P6: 극단 산술(2배 상승 후 제자리→0) + 실측 하루 급등락 잠식 + 추세 상승 복리효과
- P7: KODEX 레버리지 상장주식수(순증) — 오르면 팔고 빠지면 버티는 실증
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
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#8fa8bf'; RED='#C0392B'; BLUE='#2E5F97'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
PARQ="C:/Users/gamer38/Documents/Claude/Projects/ETF WEB/ETF_데이터_pivot.parquet"
df=pd.read_parquet(PARQ)

def px(nm,col='수정주가(원)',zero_ok=False):
    k=df[df['종목명']==nm].dropna(subset=[col]).sort_values('날짜')
    s=pd.Series(k[col].astype(float).values,index=pd.to_datetime(k['날짜']).values)
    i=pd.to_datetime(s.index); s=s[i.dayofweek<5]
    if zero_ok: return s
    chg=s.pct_change().fillna(1.0); return s[chg!=0]

k1=px('KODEX 200'); k2=px('KODEX 레버리지')
hv=px('KODEX SK하이닉스단일종목레버리지')
sh=px('KODEX 레버리지','상장주식수(주)',zero_ok=True)

def style(ax):
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    ax.grid(axis='y',color='#e6ebf1',lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(labelsize=9)

# ================= P5-A : KOSPI200 4년 5개월 왕복 =================
t0,t1=pd.Timestamp('2020-12-30'),pd.Timestamp('2025-05-28')
w1=k1[(k1.index>=t0)&(k1.index<=t1)]; w2=k2[(k2.index>=t0)&(k2.index<=t1)]
r1=w1/w1.iloc[0]*100; r2=w2/w2.iloc[0]*100
print(f"[P5-A] {t0.date()}~{t1.date()}: 기초 {r1.iloc[-1]-100:+.1f}% · 레버리지 {r2.iloc[-1]-100:+.1f}%")
fig,ax=plt.subplots(figsize=(5.5,3.55),dpi=150)
ax.plot(r1.index,r1.values,color=NAVY,lw=1.8,label='KOSPI200 (KODEX 200)')
ax.plot(r2.index,r2.values,color=RED,lw=1.8,label='KODEX 레버리지 (2배)')
ax.axhline(100,color='#b8c6d4',lw=1.0,ls='--')
ax.annotate(f"지수 {r1.iloc[-1]-100:+.1f}% (제자리)",xy=(r1.index[-1],r1.iloc[-1]),xytext=(-118,14),
            textcoords='offset points',fontsize=10.5,fontweight='bold',color=NAVY)
ax.annotate(f"레버리지 {r2.iloc[-1]-100:+.1f}%",xy=(r2.index[-1],r2.iloc[-1]),xytext=(-105,-22),
            textcoords='offset points',fontsize=10.5,fontweight='bold',color=RED)
ax.set_title("KOSPI200 왕복 4년 5개월 (2020.12.30 → 2025.05.28)",fontsize=11,fontweight='bold',color='#222')
ax.legend(fontsize=8.5,loc='upper left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m')); style(ax)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_long_k200.png')); plt.close()

# ================= P5-B : 하이닉스레버리지 출시가 복귀 + 왕복 창 =================
h=hv[hv.index>=pd.Timestamp('2026-05-27')]
h=h[h.index<=pd.Timestamp('2026-07-15')]
hb=(1.0+h.pct_change().fillna(0)/2.0).cumprod()*100   # 기초 역산: 일별수익률÷2
hl=h/h.iloc[0]*100
tR=pd.Timestamp('2026-07-03')
print(f"[P5-B] 출시 {h.index[0].date()} {h.iloc[0]:,.0f}원 → {tR.date()}: 레버리지 {hl[tR]-100:+.1f}% vs 기초 {hb[tR]-100:+.1f}%")
a,b=pd.Timestamp('2026-06-05'),pd.Timestamp('2026-07-15')
gb=float(hb[b]/hb[a]-1)*100; gl=float(hl[b]/hl[a]-1)*100
print(f"[P5-B] 왕복 창 {a.date()}~{b.date()}: 기초 {gb:+.1f}% · 레버리지 {gl:+.1f}%")
fig,ax=plt.subplots(figsize=(5.5,3.55),dpi=150)
ax.axvspan(a,b,color='#fdeede',zorder=0)
ax.plot(hb.index,hb.values,color=NAVY,lw=1.8,label='SK하이닉스 (역산, ÷2)')
ax.plot(hl.index,hl.values,color=RED,lw=1.8,label='하이닉스 레버리지 ETF (2배)')
ax.axhline(100,color='#b8c6d4',lw=1.0,ls='--')
ax.scatter([tR],[hl[tR]],s=42,color=RED,zorder=5)
ax.annotate(f"출시가 복귀 {tR.strftime('%m.%d')}\n레버리지 {hl[tR]-100:+.1f}% vs 주가 {hb[tR]-100:+.1f}%",
            xy=(tR,hl[tR]),xytext=(-172,-76),textcoords='offset points',fontsize=9,fontweight='bold',color=RED,
            arrowprops=dict(arrowstyle='-',color=RED,lw=0.9))
ax.annotate(f"왕복 창 {a.strftime('%m.%d')}~{b.strftime('%m.%d')} :\n주가 {gb:+.1f}% · 레버리지 {gl:+.1f}%",
            xy=(pd.Timestamp('2026-07-01'),148),fontsize=9,fontweight='bold',color='#b45309',ha='left')
ax.set_ylim(45,168)
ax.set_title("하이닉스 레버리지 ETF (2026.05.27 상장 ~ 07.15)",fontsize=11,fontweight='bold',color='#222')
ax.legend(fontsize=8.5,loc='upper left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%d')); style(ax)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_hynix_rt.png')); plt.close()

# ================= P6-A : 극단 산술 — 2배 올랐다 제자리면 레버리지는 0 =================
fig,ax=plt.subplots(figsize=(3.7,3.5),dpi=150)
xs=[0,1,2]
ax.plot(xs,[100,200,100],color=NAVY,lw=2.2,marker='o',ms=6,label='지수')
ax.plot(xs,[100,300,0],color=RED,lw=2.2,marker='o',ms=6,label='레버리지 2배')
for x,y,t,c,dy in [(1,200,'+100%',NAVY,10),(2,100,'-50%  (제자리)',NAVY,10),
                   (1,300,'+200%',RED,10),(2,0,'-100% → 0',RED,12)]:
    ax.annotate(t,xy=(x,y),xytext=(0,dy),textcoords='offset points',ha='center',
                fontsize=10,fontweight='bold',color=c)
ax.set_xticks(xs); ax.set_xticklabels(['시작','지수 2배 상승','지수 제자리'],fontsize=9.5)
ax.set_ylim(-40,345); style(ax)
ax.set_title("산술적 극단 예시",fontsize=11,fontweight='bold',color='#222')
ax.legend(fontsize=9,loc='upper left',frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_arith0.png')); plt.close()

# ================= P6-B : 실측 — 하루 +24% 급등 뒤 하락 (KOSPI200) =================
d1,d2,d0=pd.Timestamp('2026-07-31'),pd.Timestamp('2026-08-03'),pd.Timestamp('2026-07-30')
b1=float(k1[d1]/k1[d0]-1); b2=float(k1[d2]/k1[d1]-1); bc=float(k1[d2]/k1[d0]-1)
l1=float(k2[d1]/k2[d0]-1); l2=float(k2[d2]/k2[d1]-1); lc=float(k2[d2]/k2[d0]-1)
print(f"[P6-B] 7/31 지수 {b1*100:+.1f}% (lev {l1*100:+.1f}%) → 8/3 {b2*100:+.1f}% (lev {l2*100:+.1f}%)")
print(f"       이틀 누적: 지수 {bc*100:+.1f}% · 단순2배 {bc*200:+.1f}% · 레버리지 실제 {lc*100:+.1f}% → 잠식 {lc*100-bc*200:+.1f}%p")
fig,ax=plt.subplots(figsize=(3.7,3.5),dpi=150)
gl_=['7/31\n급등','8/3\n하락','이틀 누적']
xi=np.arange(3); wdt=0.38
bv=[b1*100,b2*100,bc*200]; lv=[l1*100,l2*100,lc*100]
bars1=ax.bar(xi-wdt/2,bv,wdt,color=SKY,label='지수 (누적은 단순 2배)')
bars2=ax.bar(xi+wdt/2,lv,wdt,color=RED,label='KODEX 레버리지 실제')
for r in list(bars1)+list(bars2):
    v=r.get_height()
    ax.annotate(f"{v:+.1f}",xy=(r.get_x()+r.get_width()/2,v),xytext=(0,4 if v>=0 else -13),
                textcoords='offset points',ha='center',fontsize=8.6,fontweight='bold',
                color='#3c576e' if r in list(bars1) else RED)
ax.annotate(f"이틀 만에 {lc*100-bc*200:+.1f}%p 잠식",xy=(2,max(bc*200,lc*100)),xytext=(0,22),
            textcoords='offset points',ha='center',fontsize=9.5,fontweight='bold',color='#b45309')
ax.set_xticks(xi); ax.set_xticklabels(gl_,fontsize=9); ax.axhline(0,color='#888',lw=0.8)
ax.set_ylim(min(min(bv),min(lv))-8,max(max(bv),max(lv))+14)
style(ax); ax.set_title("실측 : 하루 +24% 급등 직후 (2026.07)",fontsize=11,fontweight='bold',color='#222')
ax.legend(fontsize=8,loc='upper right',frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_spike.png')); plt.close()

# ================= P6-C : 그러나 추세 상승장에선 복리 효과 =================
u0,u1=pd.Timestamp('2025-04-30'),pd.Timestamp('2026-06-22')
w1=k1[(k1.index>=u0)&(k1.index<=u1)]; w2=k2[(k2.index>=u0)&(k2.index<=u1)]
rb=w1/w1.iloc[0]; rl=w2/w2.iloc[0]
simple=1.0+(rb-1.0)*2.0   # 단순 2배 (재조정 없는 가상)
print(f"[P6-C] {u0.date()}~{u1.date()}: 기초 {float(rb.iloc[-1])*100-100:+.1f}% · 레버리지 {float(rl.iloc[-1])*100-100:+.1f}% · 단순2배 {float(simple.iloc[-1])*100-100:+.1f}% → 복리효과 {(float(rl.iloc[-1])-float(simple.iloc[-1]))*100:+.1f}%p")
# 참고: 2020 추세장
v0,v1=pd.Timestamp('2020-03-23'),pd.Timestamp('2021-01-11')
q1=k1[(k1.index>=v0)&(k1.index<=v1)]; q2=k2[(k2.index>=v0)&(k2.index<=v1)]
qb=float(q1.iloc[-1]/q1.iloc[0]-1); ql=float(q2.iloc[-1]/q2.iloc[0]-1)
print(f"[P6-C 참고] {v0.date()}~{v1.date()}: 기초 {qb*100:+.1f}% · 레버리지 {ql*100:+.1f}% · 단순2배 {qb*200:+.1f}% → +{(ql-2*qb)*100:.1f}%p")
fig,ax=plt.subplots(figsize=(3.7,3.5),dpi=150)
ax.plot(rl.index,rl.values*100,color=ORANGE,lw=2.0,label='레버리지 실제 (복리)')
ax.plot(simple.index,simple.values*100,color=GRAY,lw=1.7,ls='--',label='단순 2배 (가상)')
ax.plot(rb.index,rb.values*100,color=NAVY,lw=1.5,label='지수')
ax.annotate(f"{float(rl.iloc[-1])*100-100:+,.0f}%",xy=(rl.index[-1],rl.iloc[-1]*100),xytext=(-52,-2),
            textcoords='offset points',fontsize=10,fontweight='bold',color=ORANGE)
ax.annotate(f"{float(simple.iloc[-1])*100-100:+,.0f}%",xy=(simple.index[-1],simple.iloc[-1]*100),xytext=(-50,8),
            textcoords='offset points',fontsize=9.5,fontweight='bold',color=GRAY)
ax.annotate(f"복리 효과\n{(float(rl.iloc[-1])-float(simple.iloc[-1]))*100:+,.0f}%p",
            xy=(rl.index[-40],float(rl.iloc[-40])*100),xytext=(-95,20),textcoords='offset points',
            fontsize=9.5,fontweight='bold',color='#b45309')
ax.set_title("추세 상승장 (2025.04~2026.06)",fontsize=11,fontweight='bold',color='#222')
ax.legend(fontsize=8,loc='upper left',frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m')); style(ax)
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_trend.png')); plt.close()

# ================= P7 : 상장주식수(순증) 실증 =================
shm=sh.resample('ME').last(); k1m=k1.resample('ME').last()
common=shm.index.intersection(k1m.index)
shm=shm[common]; k1m=k1m[common]
dsh=shm.pct_change().dropna(); dk=k1m.pct_change().dropna()
cm=dsh.index.intersection(dk.index); dsh=dsh[cm]; dk=dk[cm]
corr=float(np.corrcoef(dk.values,dsh.values)[0,1])
up=dsh[dk>0.02]; dn=dsh[dk<-0.02]
print(f"[P7] 월간 상관(지수수익 vs 주식수증감) {corr:+.2f} · 지수 +2%↑월 평균 주식수 {up.mean()*100:+.1f}% · -2%↓월 {dn.mean()*100:+.1f}% (n={len(up)}/{len(dn)})")
# 에피소드
def episode(a,b,label):
    s0,s1=float(sh[sh.index>=a].iloc[0]),float(sh[sh.index<=b].iloc[-1])
    p0,p1=float(k1[k1.index>=a].iloc[0]),float(k1[k1.index<=b].iloc[-1])
    print(f"  · {label}: 지수 {p1/p0*100-100:+.0f}% · 주식수 {s1/s0*100-100:+.0f}% ({s0/1e6:,.0f}→{s1/1e6:,.0f}백만주)")
    return s1/s0-1,p1/p0-1
episode(pd.Timestamp('2020-01-02'),pd.Timestamp('2020-03-23'),'2020 급락')
episode(pd.Timestamp('2020-03-23'),pd.Timestamp('2021-01-11'),'2020-21 반등')
e_r=episode(pd.Timestamp('2025-04-30'),pd.Timestamp('2026-06-22'),'2025-26 추세상승')
e_c=episode(pd.Timestamp('2026-06-22'),pd.Timestamp('2026-08-12'),'2026-07 급락')
fig,ax=plt.subplots(figsize=(9.6,3.9),dpi=150)
w=(sh.index>=pd.Timestamp('2019-01-01'))
ax.fill_between(sh.index[w],sh.values[w]/1e6,color='#f3c69a',alpha=0.85,label='KODEX 레버리지 상장주식수 (백만주, 좌)')
ax.set_ylabel('상장주식수 (백만주)',fontsize=9.5,color='#b45309')
ax.tick_params(axis='y',labelcolor='#b45309')
ax2=ax.twinx()
kk=k1[k1.index>=pd.Timestamp('2019-01-01')]
ax2.plot(kk.index,kk.values/1000,color=NAVY,lw=1.6,label='KOSPI200 (KODEX 200 수정주가, 천원, 우)')
ax2.set_ylabel('KODEX 200 (천원)',fontsize=9.5,color=NAVY)
ax2.tick_params(axis='y',labelcolor=NAVY)
for spn in ['top']: ax.spines[spn].set_visible(False); ax2.spines[spn].set_visible(False)
ax.grid(axis='y',color='#eee',lw=0.6); ax.set_axisbelow(True); ax.tick_params(labelsize=9)
ymax=sh.values[w].max()/1e6
anns=[('2020 급락 :\n주식수 급증 = 저가 매수·버티기',pd.Timestamp('2020-09-20'),0.90),
      ('반등하자 환매\n(복리 구간 이탈)',pd.Timestamp('2021-05-15'),0.55),
      ('2025~26 급등 :\n주식수 급감 = 조기 환매',pd.Timestamp('2025-05-01'),0.66)]
for t,x,fy in anns:
    ax.annotate(t,xy=(x,ymax*fy),ha='center',fontsize=9,fontweight='bold',color='#8a4a08')
ax.annotate('26.07 급락하자\n다시 유입·버티기',xy=(pd.Timestamp('2026-07-25'),62),
            xytext=(pd.Timestamp('2026-03-20'),ymax*0.33),ha='center',fontsize=9,fontweight='bold',
            color='#8a4a08',arrowprops=dict(arrowstyle='-',color='#8a4a08',lw=0.9))
h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels()
ax.legend(h1+h2,l1+l2,fontsize=8.5,loc='lower left',bbox_to_anchor=(0.0,1.01),ncol=2,frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
plt.tight_layout(); plt.savefig(os.path.join(IMG,'lev15_flow.png')); plt.close()
print("차트 6종 저장 완료:",', '.join(['lev15_long_k200','lev15_hynix_rt','lev15_arith0','lev15_spike','lev15_trend','lev15_flow']))
