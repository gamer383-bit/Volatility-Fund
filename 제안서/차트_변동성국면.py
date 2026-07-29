# -*- coding: utf-8 -*-
"""1페이지 근거 차트: 시장 변동성 국면별 — 일반 주식형 ETF vs 변동성 하베스트
- 데이터: ETF_데이터_pivot.parquet (국내 상장 ETF 일별 수정주가, 2019.01~2026.07)
- 시장 변동성 = KODEX 200(A069500) 월중 일수익률 연율화
- 국면: 저변동(σ<15%) / 변동성 급등(Δσ 상위 20%) / 고변동(σ≥30%)
- 일반 ETF = 채권·금리·현금성 제외 주식형 1,081종목의 월수익률 평균 (손실 비중 병기)
- 전략 = 변동성 하베스트 성장형 백테스트(TOP2, 2021.08~) 월수익률 평균
"""
import os, platform, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#9db4cc'; RED='#C0392B'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')

df=pd.read_parquet("C:/Users/gamer38/Documents/Claude/Projects/ETF WEB/ETF_데이터_pivot.parquet")
df=df.dropna(subset=['수정주가(원)'])
df['날짜']=pd.to_datetime(df['날짜'])
df['ym']=df['날짜'].dt.to_period('M')
FI=['채권','국고','금리','단기','머니','KOFR','통안','회사채','크레딧','국공채','은행채','전단채','CD','SOFR','달러단기','캐리','TRF','TDF','채혼']
names=df[['종목코드','종목명']].drop_duplicates('종목코드')
eq=set(names[~names['종목명'].str.contains('|'.join(FI),case=False,na=False)]['종목코드'])
d2=df[df['종목코드'].isin(eq)]
last=d2.sort_values('날짜').groupby(['종목코드','ym'])['수정주가(원)'].last().unstack()
mret=last.pct_change(axis=1)

k=df[df['종목코드']=='A069500'].sort_values('날짜')
kr=k.set_index('날짜')['수정주가(원)'].pct_change().dropna()
mvol=kr.groupby(kr.index.to_period('M')).std()*np.sqrt(252)*100
mvol=mvol[mvol.index>=pd.Period('2019-01')]
dvol=mvol.diff()
thr=dvol.quantile(0.8)
REG=[('저변동\n(σ<15%)',mvol[mvol<15].index),
     ('변동성 급등\n(Δσ 상위 20%)',dvol[dvol>=thr].index),
     ('고변동\n(σ≥30%)',mvol[mvol>=30].index)]

etf_mean=[]; etf_loss=[]
for lb,ms in REG:
    sub=mret[mret.columns.intersection(ms)].stack().dropna()
    etf_mean.append(sub.mean()*100); etf_loss.append((sub<0).mean()*100)

# 전략(성장형) 월수익률 — 백테스트_턴.py의 simulate 재사용
src=open(os.path.join(BASE,'백테스트_턴.py'),encoding='utf-8').read().split('results={}')[0]
src=src.replace("sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')","")
exec(src)
turns,G=simulate('g')
gv=pd.Series(G['V'],index=pd.DatetimeIndex(G['d']))
gm=gv.groupby(gv.index.to_period('M')).last().pct_change().dropna()
st_mean=[float(gm[gm.index.isin(ms)].mean()*100) for _,ms in REG]

for (lb,ms),em,el,sm in zip(REG,etf_mean,etf_loss,st_mean):
    print(f"{lb.replace(chr(10),' ')}: ETF 평균 {em:+.2f}%/월 (손실 비중 {el:.0f}%) | 전략 {sm:+.2f}%/월")

def draw_card():
    """1페이지 4번째 카드용 세로형 (aspect ≈ 0.83)"""
    x=np.arange(3); wd=0.35
    fig,ax=plt.subplots(figsize=(5.0,6.0),dpi=150)
    ax.bar(x-wd/2,etf_mean,wd,color=SKY,label='일반 주식형 ETF 평균')
    ax.bar(x+wd/2,st_mean,wd,color=ORANGE,label='변동성 하베스트(성장형)')
    ax.axhline(0,color='#666',lw=1.0)
    for xi,(em,el) in enumerate(zip(etf_mean,etf_loss)):
        va='bottom' if em>=0 else 'top'; off=0.14 if em>=0 else -0.14
        ax.text(xi-wd/2,em+off,f"{em:+.1f}%",ha='center',va=va,fontsize=13,color='#40566e',fontweight='bold')
        ax.text(xi,-2.15,f"손실 ETF {el:.0f}%",ha='center',fontsize=11,
                color=(RED if el>=50 else GRAY),fontweight='bold')
    for xi,sm in enumerate(st_mean):
        ax.text(xi+wd/2,sm+0.14,f"{sm:+.1f}%",ha='center',va='bottom',fontsize=14.5,color=ORANGE,fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['저변동\n(σ<15%)','변동성 급등\n(Δσ 상위20%)','고변동\n(σ≥30%)'],fontsize=11.5,color=NAVY)
    ax.set_ylabel('월평균 수익률 (%)',fontsize=12,color=NAVY)
    ax.set_ylim(-2.6,max(st_mean)+1.5)
    ax.grid(alpha=0.22,axis='y'); ax.spines[['top','right']].set_visible(False)
    ax.tick_params(axis='y',labelsize=10.5)
    ax.legend(fontsize=10.5,frameon=False,loc='upper left')
    fig.text(0.5,0.012,'주식형 ETF 1,081종목 × 91개월(2019.01~2026.07)\n시장 변동성=KODEX 200 · 데이터: ETF_데이터_pivot',
             ha='center',color=GRAY,fontsize=8.0)
    fig.tight_layout(rect=[0,0.055,1,1])
    fig.savefig(os.path.join(IMG,'vol_regime_card.png'),bbox_inches='tight'); plt.close(fig)
    print("saved vol_regime_card.png")
draw_card()

x=np.arange(3); wd=0.34
fig,ax=plt.subplots(figsize=(8.6,4.6),dpi=140)
b1=ax.bar(x-wd/2,etf_mean,wd,color=SKY,label='일반 주식형 ETF 평균 (1,081종목)')
b2=ax.bar(x+wd/2,st_mean,wd,color=ORANGE,label='변동성 하베스트 (성장형 백테스트)')
ax.axhline(0,color='#666',lw=1.0)
for xi,(em,el) in enumerate(zip(etf_mean,etf_loss)):
    va='bottom' if em>=0 else 'top'; off=0.12 if em>=0 else -0.12
    ax.text(xi-wd/2,em+off,f"{em:+.1f}%",ha='center',va=va,fontsize=11.5,color='#40566e',fontweight='bold')
    ax.text(xi-wd/2,-2.05,f"손실 ETF {el:.0f}%",ha='center',fontsize=9.5,color=(RED if el>=50 else GRAY),fontweight='bold')
for xi,sm in enumerate(st_mean):
    ax.text(xi+wd/2,sm+0.12,f"{sm:+.1f}%",ha='center',va='bottom',fontsize=12.5,color=ORANGE,fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([lb for lb,_ in REG],fontsize=11.5,color=NAVY)
ax.set_ylabel('월평균 수익률 (%)',fontsize=11.5,color=NAVY)
ax.set_ylim(-2.4,max(st_mean)+1.2)
ax.set_title('시장 변동성 국면별 성과 — 일반 ETF는 부진, 변동성 하베스트는 확대',
             fontsize=13.5,color=NAVY,fontweight='bold',loc='left',pad=10)
ax.grid(alpha=0.22,axis='y'); ax.spines[['top','right']].set_visible(False)
ax.tick_params(axis='y',labelsize=10)
ax.legend(fontsize=10,frameon=False,loc='upper left')
fig.text(0.99,0.01,'시장 변동성=KODEX 200 월중 일수익률 연율화(2019.01~2026.07, 91개월) · ETF=채권·금리·현금성 제외 주식형 월수익률 · 전략=TOP2 백테스트(2021.08~) · 데이터: ETF_데이터_pivot',
         ha='right',color=GRAY,fontsize=7.2)
fig.tight_layout(rect=[0,0.03,1,1])
fig.savefig(os.path.join(IMG,'vol_regime_evidence.png'),bbox_inches='tight'); plt.close(fig)
print("saved vol_regime_evidence.png")
