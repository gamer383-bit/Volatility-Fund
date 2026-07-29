# -*- coding: utf-8 -*-
"""K200 제안서 15~17페이지: QPMS 화면 스타일 이미지 3장 (KOSPI200 · 옵션 용어 배제)
- bp_k2_growth.png / bp_k2_stable.png : 진입 청사진 (오늘 신규 1년 턴, 변동성 50% 기준 초기 편입비)
- monitor_k2.png : 현재 모니터링 (기준일 2026-07-27, 백테스트 엔진 실측 상태값)
값 출처: 백테스트_턴_k200.py (σ 롤링 상한 60%) · 초기 편입비는 σ50% 가정
"""
import os, platform, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
IMG=os.path.join(os.path.dirname(os.path.abspath(__file__)),'img')
NAVY='#043B72'; ORANGE='#E8720C'; BLUE='#1f5fa8'; GRAY='#84888B'
BORDER='#d5dde6'; HEAD='#eef3f9'; TXT='#3a3a3a'

PX=945.69; PXD='2026-07-28'   # KOSPI200 종가 (엑셀, 사용자 제공)

def blueprint(fname,prod,color,w0,figh):
    fig=plt.figure(figsize=(11.9,figh),dpi=150)
    ax=fig.add_axes([0,0,1,1]); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100)
    ax.add_patch(FancyBboxPatch((0.4,2),99.2,96,boxstyle='round,pad=0.1,rounding_size=1.2',
                 fc='#f4f7fb',ec=BORDER,lw=1.2))
    ax.text(2,88,'진입 청사진 — 오늘 신규 1년 턴 개시 (정규화 지수 100 · τ=1.0)',
            fontsize=13,fontweight='bold',color=NAVY,va='top')
    ax.text(2,70,'운용액(AUM)  100억',fontsize=11,color=TXT,fontweight='bold',va='top')
    ax.text(15,70,'진입가 = 오늘 종가. 현금 잔여(1-편입비)는 이자 수취.',fontsize=9.5,color=GRAY,va='top')
    # 표
    cols=[('상품',3),('편입자산',26),('목표 편입비',52),('금액(억)',70),('잔여 현금(억)',86)]
    ax.add_patch(Rectangle((1.5,44),97,12,fc=HEAD,ec=BORDER,lw=0.8))
    for t,x in cols: ax.text(x,50,t,fontsize=10,color=BLUE,fontweight='bold',va='center')
    ax.add_patch(Rectangle((1.5,28),97,16,fc='white',ec=BORDER,lw=0.8))
    vals=[(prod,3,color,True),('KOSPI200 현물 바스켓',26,TXT,False),
          (f'{w0:.1f}%',52,TXT,True),(f'{w0:.1f}',70,TXT,False),(f'{100-w0:.1f} (연 2.5%)',86,TXT,False)]
    for t,x,c,b in vals: ax.text(x,36,t,fontsize=10.5,color=c,fontweight=('bold' if b else 'normal'),va='center')
    ax.text(2,16,f'진입가(오늘 종가): KOSPI200 {PX:,.2f} ({PXD}) · 목표 편입비는 QPMS 산식(기본가정 변동성 50%)으로 일별 재산출 · 이자 r=2.5% 수취',
            fontsize=9.5,color=GRAY,va='top')
    fig.savefig(os.path.join(IMG,fname)); plt.close(fig)
    print("saved",fname)

blueprint('bp_k2_growth.png','상품1(상승노출형)',ORANGE,60.0,2.04)
blueprint('bp_k2_stable.png','상품2(안정형)',BLUE,43.1,1.93)

# ---- 현재 모니터링 (기준일 2026-07-27, 엔진 실측) ----
fig=plt.figure(figsize=(8.75,5.0),dpi=150)
ax=fig.add_axes([0,0,1,1]); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100)
ax.add_patch(Rectangle((0,0),100,100,fc='#f4f7fb',ec=BORDER,lw=1.0))
# 탭 바
ax.add_patch(Rectangle((0,92.5),100,7.5,fc='white',ec=BORDER,lw=0.8))
for t,x,on in (('현재 모니터링',2,True),('과거 모니터링',16,False),('성과 시계열',30,False),('월별성과',42,False)):
    ax.text(x,96,t,fontsize=9.5,color=(NAVY if on else GRAY),fontweight=('bold' if on else 'normal'),va='center')
ax.plot([1.5,13],[92.9,92.9],color=ORANGE,lw=2.5)
# KPI 카드 (상품별)
def card(x,w,title,val,color,sub=''):
    ax.add_patch(FancyBboxPatch((x,72),w,16,boxstyle='round,pad=0.15,rounding_size=0.8',fc='white',ec=BORDER,lw=1.0))
    ax.text(x+w/2,84.5,title,fontsize=8.2,color=GRAY,ha='center',va='center')
    ax.text(x+w/2,78,val,fontsize=12.5,color=color,fontweight='bold',ha='center',va='center')
    if sub: ax.text(x+w/2,73.6,sub,fontsize=7.2,color=GRAY,ha='center',va='center')
card(2,14,'기준일','2026-07-27',NAVY)
card(17.5,19,'상품1(상승노출형)','턴9 · 41일차',ORANGE,'지수 S 82.3 · 잔존 0.83년')
card(38,13,'상품1 편입비','74.7%',ORANGE)
card(52.5,13,'상품1 누적 NAV','173.7',ORANGE,'설정=100')
card(67,13,'상품2 편입비','60.0%',BLUE,'턴7 · S 78.6')
card(81.5,16,'상품2 누적 NAV','121.9',BLUE,'설정=100')
# 보유 포지션 표
ax.add_patch(FancyBboxPatch((2,26),95.5,42,boxstyle='round,pad=0.15,rounding_size=0.8',fc='white',ec=BORDER,lw=1.0))
ax.text(4,63.5,'보유 포지션 (AUM 각 100억 가정)',fontsize=10.5,color=TXT,fontweight='bold',va='center')
cols=[('상품',5),('편입자산',30),('편입비',56),('금액(억)',70),('잔여 현금(억)',84)]
ax.add_patch(Rectangle((4,53),91.5,6.5,fc=HEAD,ec=BORDER,lw=0.6))
for t,x in cols: ax.text(x,56.2,t,fontsize=8.8,color=BLUE,fontweight='bold',va='center')
rows=[('상품1(상승노출형)',ORANGE,'KOSPI200 현물 바스켓','74.7%','74.7','25.3'),
      ('상품2(안정형)',BLUE,'KOSPI200 현물 바스켓','60.0%','60.0','40.0')]
for i,(p,c,a,wv,mv,cv) in enumerate(rows):
    y0=46.5-i*7
    ax.add_patch(Rectangle((4,y0-3.2),91.5,6.6,fc='white',ec=BORDER,lw=0.5))
    ax.text(5,y0,p,fontsize=8.8,color=c,fontweight='bold',va='center')
    ax.text(30,y0,a,fontsize=8.8,color=TXT,va='center')
    for t,x in ((wv,56),(mv,70),(cv,84)): ax.text(x,y0,t,fontsize=8.8,color=TXT,va='center')
ax.text(4,31,f'지수: KOSPI200 1,069.22 (2026-07-27 종가) · 편입비×AUM=금액 · 잔여 현금은 연 2.5% 수취',
        fontsize=7.8,color=GRAY,va='center')
# 하락 관리 단계 (옵션 용어 배제)
ax.text(4,21.5,'하락 관리 단계 (상품1 턴 설정일 지수=100 기준)',fontsize=10,color=TXT,fontweight='bold',va='center')
stages=[('① 정상 (S>80)',True),('② 주의 (S≤80)',False),('③ 심화 하락 (S≤70)',False),('④ 주식형 전환 (S≤60)',False)]
for i,(t,on) in enumerate(stages):
    x=4+i*23.5
    ax.add_patch(FancyBboxPatch((x,10),21.5,7,boxstyle='round,pad=0.15,rounding_size=0.9',
                 fc=(ORANGE if on else '#eceff3'),ec=BORDER,lw=0.8))
    ax.text(x+10.75,13.5,t,fontsize=8.6,color=('white' if on else GRAY),fontweight=('bold' if on else 'normal'),ha='center',va='center')
ax.text(4,5,'전환 기준: 턴 설정일 지수 대비 -40%(S≤60) 도달 시 상승 수취 중심의 주식형 운용으로 전환 · 현재 S=82.3 → ① 정상',
        fontsize=7.8,color=GRAY,va='center')
fig.savefig(os.path.join(IMG,'monitor_k2.png')); plt.close(fig)
print("saved monitor_k2.png")
