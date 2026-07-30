# -*- coding: utf-8 -*-
"""K200 제안서 2페이지: KOSPI200 실현변동성 추이 (60영업일 연율화, 최근 5년)
슬롯 9.20×4.14in (aspect 2.22) → figsize (10.0, 4.5)"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; RED='#C0392B'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

raw=pd.read_excel(XLS,sheet_name='코스피_코스피200_코스닥150',header=None)
d=raw.iloc[14:]
s=pd.Series(pd.to_numeric(d.iloc[:,2],errors='coerce').values,index=pd.to_datetime(d.iloc[:,0]).values).dropna().sort_index()
i=pd.to_datetime(s.index); s=s[i.dayofweek<5]
chg=s.pct_change().fillna(1.0); s=s[chg!=0]
ret=s.pct_change().dropna(); lr=np.log(1+ret)
v60=(lr.rolling(60).std()*math.sqrt(252)*100).dropna()
avg=v60.mean(); cur=v60.iloc[-1]
print(f"KOSPI200 60일 변동성: 최근 {cur:.0f}% · 5년평균 {avg:.0f}% · 최대 {v60.max():.0f}%")

fig,ax=plt.subplots(figsize=(10.0,4.5),dpi=140)
ax.plot(v60.index,v60.values,color=NAVY,lw=1.9)
ax.fill_between(v60.index,0,v60.values,color=NAVY,alpha=0.08)
ax.axhline(avg,color=GRAY,ls='--',lw=1.3)
ax.text(v60.index[5],avg+1.5,f'5년 평균 {avg:.0f}%',color=GRAY,fontsize=11,fontweight='bold')
ax.plot([v60.index[-1]],[cur],'o',color=RED,ms=9,zorder=5)
ax.annotate(f'현재 {cur:.0f}%\n(역대 최고)',xy=(v60.index[-1],cur),xytext=(-95,-14),
            textcoords='offset points',color=RED,fontsize=13.5,fontweight='bold',
            arrowprops=dict(arrowstyle='->',color=RED,lw=1.5))
ax.set_ylabel('실현변동성 (연율화, %)',color=NAVY,fontsize=11.5)
ax.set_ylim(0,max(v60.max()*1.12,85))
ax.set_title(f'KOSPI200 실현변동성 (직전 60영업일 연율화) — 현재 {cur:.0f}%, 5년 평균({avg:.0f}%)의 {cur/avg:.1f}배',
             color=NAVY,fontsize=14,fontweight='bold',loc='left',pad=10)
ax.grid(alpha=0.22); ax.spines[['top','right']].set_visible(False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
ax.tick_params(labelsize=10)
fig.text(0.99,0.01,f'데이터: KOSPI200 종가지수 {v60.index[0].date()}~{v60.index[-1].date()} (주말·휴장 제외)',
         ha='right',color=GRAY,fontsize=8)
fig.tight_layout(rect=[0,0.03,1,1])
fig.savefig(os.path.join(IMG,'vol_k200.png'),bbox_inches='tight'); plt.close(fig)
print("saved vol_k200.png")
