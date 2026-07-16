# -*- coding: utf-8 -*-
"""7페이지 차트: KODEX 하이닉스레버리지 — 상장 후 실제 성과와 리밸런싱 (ETF_데이터_pivot)
- 기간: 상장 2026-05-27 ~ parquet 최신일(자동), 시작=0%
- 기초(1배)는 레버리지 일별수익률 ÷2 역산(근사), 단순2배=기초 누적×2
- 하단: 이론 매매 = 2×일수익률 (상승일 매수/하락일 매도, 순자산 %)
- 하단 캡션에 데이터 기준일 명시(필수)
"""
import os, platform, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; RED='#C0392B'; BLUE='#2980B9'; GRAY='#84888B'
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'img')

df=pd.read_parquet("C:/Users/gamer38/Documents/Claude/Projects/ETF WEB/ETF_데이터_pivot.parquet")
k=df[df['종목명']=='KODEX SK하이닉스단일종목레버리지'].dropna(subset=['수정주가(원)']).sort_values('날짜')
k=k[k['날짜']>='2026-05-27']
dt=pd.to_datetime(k['날짜']); px=k['수정주가(원)'].astype(float).values
ASOF=k['날짜'].iloc[-1]
rL=px[1:]/px[:-1]-1.0                 # 레버리지 일수익률
rU=rL/2.0                              # 기초 1배 근사(역산)
cumL=np.concatenate([[0],(np.cumprod(1+rL)-1)])*100
cumU=np.concatenate([[0],(np.cumprod(1+rU)-1)])*100
simple2=2*cumU                         # 단순 2배
print(f"기간: 2026-05-27 ~ {ASOF} ({len(px)}일)")
print(f"레버리지 {cumL[-1]:+.1f}% | 기초(역산) {cumU[-1]:+.1f}% | 단순2배 {simple2[-1]:+.1f}% | 잠식 {cumL[-1]-simple2[-1]:+.1f}%p")

fig,(ax1,ax2)=plt.subplots(2,1,figsize=(7.67,5.71),dpi=100,height_ratios=[1.6,1],sharex=True)
ax1.plot(dt,cumU,color=NAVY,lw=2.2,label='SK하이닉스 (기초, 1배 역산)')
ax1.plot(dt,cumL,color=RED,lw=2.2,label='KODEX 하이닉스레버리지')
ax1.axhline(0,color='#9db4cc',lw=0.9)
ax1.annotate(f'{cumL[-1]:+.1f}%',xy=(dt.iloc[-1],cumL[-1]),xytext=(6,0),textcoords='offset points',color=RED,fontsize=13,fontweight='bold',va='center')
ax1.annotate(f'{cumU[-1]:+.1f}%',xy=(dt.iloc[-1],cumU[-1]),xytext=(6,0),textcoords='offset points',color=NAVY,fontsize=13,fontweight='bold',va='center')
ylo=min(cumL.min(),cumU.min())
ax1.text(dt.iloc[3],ylo+1,f'단순 2배({simple2[-1]:+.0f}%)에 못 미침 = 변동성 잠식 {cumL[-1]-simple2[-1]:+.1f}%p',
         color=RED,fontsize=11.5,fontweight='bold')
# 기초가 상장가 부근으로 복귀한 가장 최근 시점 표시 (|기초|≤4%) — 순수 변동성 잠식 사례
flat=[i for i in range(1,len(cumU)) if abs(cumU[i])<=4.0]
if flat:
    fi=flat[-1]
    ax1.plot([dt.iloc[fi]],[cumU[fi]],'o',color=NAVY,ms=8,zorder=5)
    ax1.plot([dt.iloc[fi]],[cumL[fi]],'o',color=RED,ms=8,zorder=5)
    ax1.annotate(f"{pd.Timestamp(dt.iloc[fi]).strftime('%m/%d')} 기초 {cumU[fi]:+.1f}% '제자리'\n레버리지 {cumL[fi]:+.1f}% = 변동성 잠식",
                 xy=(dt.iloc[fi],cumL[fi]),xytext=(-105,95),textcoords='offset points',
                 color=RED,fontsize=10.5,fontweight='bold',
                 arrowprops=dict(arrowstyle='->',color=RED,lw=1.2))
    print(f"제자리 복귀 표시: {dt.iloc[fi]} 기초 {cumU[fi]:+.1f}% / 레버리지 {cumL[fi]:+.1f}%")
ax1.set_ylabel('수익률 (%)',color=NAVY,fontsize=12)
ax1.set_title('KODEX 하이닉스레버리지 — 상장 후 실제 성과와 리밸런싱',color=NAVY,fontsize=14.5,fontweight='bold',loc='left',pad=10)
ax1.legend(fontsize=10.5,frameon=False,loc='upper left')
ax1.grid(alpha=0.2); ax1.spines[['top','right']].set_visible(False)
ax1.margins(x=0.02);
# 우측 라벨 공간
ax1.set_xlim(dt.iloc[0],dt.iloc[-1]+pd.Timedelta(days=4))

# 이론 매매(순자산 %) = 2×'기초' 일수익률 = rL (레버리지 일수익률 그 자체)
# [검증] 목표노출 2(1+2r)−현재노출 2(1+r)=2r (r=기초수익률). 기초 10% 변동 → 매매 20%.
trade=2*rU*100
cols=[RED if v>0 else BLUE for v in trade]
ax2.bar(dt.iloc[1:],trade,color=cols,width=0.8)
ax2.axhline(0,color='#555',lw=0.9)
import matplotlib.patches as mpatches
ax2.legend(handles=[mpatches.Patch(color=RED,label='상승일 매수(고가매수)'),
                    mpatches.Patch(color=BLUE,label='하락일 매도(저가매도)')],
           fontsize=9.5,frameon=False,loc='upper left')
ax2.set_ylabel('이론 매매\n(순자산 %)',color=NAVY,fontsize=11)
ax2.grid(alpha=0.2); ax2.spines[['top','right']].set_visible(False)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
fig.text(0.98,0.012,f'데이터 기준일: {ASOF} (2026-05-27~{ASOF}) · 이론매매=2×기초 일수익률 · 기초(1배)=레버리지 일수익률 역산 · ETF_데이터_pivot',
         ha='right',color=GRAY,fontsize=8.0)
fig.tight_layout(rect=[0,0.035,1,1])
fig.savefig(os.path.join(IMG,'lev_rebal_hynix.png')); plt.close(fig)
print("saved lev_rebal_hynix.png")
