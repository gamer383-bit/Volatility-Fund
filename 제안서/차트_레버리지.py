# -*- coding: utf-8 -*-
"""제안서 5페이지 차트 2종 (2026-06-30 기준)
① lev_aum.png  : 삼성전자·SK하이닉스 레버리지 ETF 글로벌 취합 (국내+홍콩+영국)
② idx_weight.png: 두 종목의 KOSPI200 내 비중 추이 (연초→5/13→6/30 추정)

출처
- 국내: ETF_데이터_pivot.parquet 2026-06-30 순자산 (하이닉스 10.12조 7종목 / 삼성 5.82조 7종목)
- 홍콩 CSOP: 서울경제 2026-06-24 (6/23 기준, 하이닉스 $122.3억=18.60조 / 삼성 $33.1억=5.02조)
- 영국 Leverage Shares(3x, 6/12 상장): 6/23 기준 하이닉스 200억·삼성 23억 (합계 0.02조)
- 미국: SK하이닉스 ADR 7/10 나스닥 상장, 레버리지 ETF는 7월 출시(6/30 기준 불포함)
- K200 비중: 아시아경제(5/13 확정 51.5%=삼성28.0+하이닉스23.5) 앵커,
  6/30은 가격변동 반영 추정(삼성 29.3% + 하이닉스 28.1% = 57.4%, 6월 정기변경 유동비 미반영)
"""
import os, platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; DRED='#C0392B'; GRAY='#84888B'; LORANGE='#FDEBD9'; CYAN='#0086B8'
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'img')

# ---------- ① 글로벌 레버리지 ETF 취합 (조원) ----------
# (국내 6/30 parquet, 홍콩·영국 6/23 언론보도)
hy=[10.12,18.60,0.02]   # 하이닉스: 국내/홍콩/영국
sa=[5.82,5.02,0.002]    # 삼성전자
labels=['국내 상장\n(16종, 6/30)','홍콩 CSOP\n(6/23)','영국 3x ETP\n(6/23)']
fig,ax=plt.subplots(figsize=(7.3,6.0),dpi=100)
xpos=np.arange(3); w=0.38
b1=ax.bar(xpos-w/2,hy,w,color=DRED,label='SK하이닉스')
b2=ax.bar(xpos+w/2,sa,w,color=ORANGE,label='삼성전자')
for b in list(b1)+list(b2):
    v=b.get_height()
    if v>=0.01: ax.text(b.get_x()+b.get_width()/2,v+0.35,f'{v:.1f}조',ha='center',color='#333',fontsize=13,fontweight='bold')
ax.set_xticks(xpos); ax.set_xticklabels(labels,fontsize=12.5)
ax.set_ylabel('레버리지 ETF 순자산 (조원)',color=NAVY,fontsize=13)
ax.set_title('삼성전자·SK하이닉스 레버리지 ETF — 글로벌 합산 약 40조원',color=NAVY,fontsize=15.5,fontweight='bold',loc='left',pad=12)
ax.set_ylim(0,22)
ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',color='#eee'); ax.set_axisbelow(True)
ax.legend(fontsize=12.5,frameon=False,loc='upper right')
ax.text(1,20.6,'홍콩 CSOP 하이닉스 =\n세계 최대 단일종목 레버리지',ha='center',color=DRED,fontsize=11.5,fontweight='bold')
fig.text(0.99,0.012,'미국은 ADR 상장(7/10) 후 7월 출시 → 6/30 기준 불포함 · 출처: ETF_데이터_pivot(국내), 서울경제 6/24(홍콩·영국)',
         ha='right',color=GRAY,fontsize=8.7)
fig.tight_layout(rect=[0,0.035,1,1])
fig.savefig(os.path.join(IMG,'lev_aum.png')); plt.close(fig)

# ---------- ② KOSPI200 내 비중 추이 ----------
pts=[('2026 연초',38.7,None,None),('5/13\n(확정)',51.5,28.0,23.5),('6/30\n(추정)',57.4,29.3,28.1)]
fig,ax=plt.subplots(figsize=(7.3,6.0),dpi=100)
xpos=np.arange(3); w=0.5
sams=[14.0,28.0,29.3]  # 연초 개별 미공표 → 표시용 분할(합계만 라벨)
hyxs=[24.7,23.5,28.1]
# 연초는 합계만 알려져 있으므로 단일 바로 처리
ax.bar([0],[38.7],w,color='#9DB4CC')
ax.bar([1],[28.0],w,color=ORANGE,label='삼성전자')
ax.bar([1],[23.5],w,bottom=[28.0],color=DRED,label='SK하이닉스')
ax.bar([2],[29.3],w,color=ORANGE)
ax.bar([2],[28.1],w,bottom=[29.3],color=DRED)
for x,total in [(0,38.7),(1,51.5),(2,57.4)]:
    ax.text(x,total+1.2,f'{total:.1f}%',ha='center',color=NAVY,fontsize=15,fontweight='bold')
ax.text(1,28.0/2,'28.0',ha='center',color='white',fontsize=11.5,fontweight='bold')
ax.text(1,28.0+23.5/2,'23.5',ha='center',color='white',fontsize=11.5,fontweight='bold')
ax.text(2,29.3/2,'29.3',ha='center',color='white',fontsize=11.5,fontweight='bold')
ax.text(2,29.3+28.1/2,'28.1',ha='center',color='white',fontsize=11.5,fontweight='bold')
ax.set_xticks(xpos); ax.set_xticklabels([p[0] for p in pts],fontsize=12.5)
ax.set_ylabel('KOSPI200 내 합산 비중 (%)',color=NAVY,fontsize=13)
ax.set_title('삼성전자+SK하이닉스, KOSPI200의 57%(6/30 추정)',color=NAVY,fontsize=15.5,fontweight='bold',loc='left',pad=12)
ax.set_ylim(0,66)
ax.axhline(50,color='#888',ls='--',lw=1); ax.text(2.32,50.7,'50%',color=GRAY,fontsize=11)
ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',color='#eee'); ax.set_axisbelow(True)
ax.legend(fontsize=12.5,frameon=False,loc='upper left')
fig.text(0.99,0.012,'5/13 확정(아시아경제) 앵커 · 6/30은 가격변동 반영 추정(6월 정기변경 유동비 미반영) · 코스피 전체 기준 54.8%(6/19, KRX)',
         ha='right',color=GRAY,fontsize=8.7)
fig.tight_layout(rect=[0,0.035,1,1])
fig.savefig(os.path.join(IMG,'idx_weight.png')); plt.close(fig)
print("saved lev_aum.png, idx_weight.png (기준 2026-06-30)")
