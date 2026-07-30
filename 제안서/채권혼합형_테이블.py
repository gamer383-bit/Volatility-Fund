# -*- coding: utf-8 -*-
"""변동성 하베스트 채권혼합형 (공모·오픈형) — 편입비·예상수익률 테이블 (100% 기준)
구조(사용자 지정): ATM 풋매도(행사가 100) + 콜스프레드 매수(110/150), 만기 3개월 고정,
행사가는 3개월마다 그 시점 지수로 리셋. BM = TOP2 40% + 1년채권.
가정: σ=60%(Top2 MC 가정), r=q=2.5%, 시뮬레이션은 100% 기준(주식 편입비 배분은 추후 결정),
     편입비 = 구조화 델타 [하한 10%], 예상수익률 = 구조화 이론손익(원금 대비, 기존 테이블 규약)
표 A: 단일 3개월 구조 — 잔존 3.0~0.5개월(0.5개월 단위) + 만기
표 B: 3개월 리셋 방식 — 매 분기 지수가 L% 변동을 반복한다고 가정 시 3/6/9/12개월 누적
"""
import sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from scipy.special import ndtr as Nv

SIG=0.60; R,Q=0.025,0.025; T=0.25
KP,K1,K2=100.,110.,150.
WMIN=0.10; WMAX=1.80

def N1(x): return float(Nv(x))
def bsd(t,S,K,tau):
    sq=SIG*math.sqrt(tau); d1=(math.log(S/K)+0.5*SIG*SIG*tau)/sq
    e=math.exp(-Q*tau); return e*N1(d1) if t=='c' else e*(N1(d1)-1)
def bsp(t,S,K,tau):
    sq=SIG*math.sqrt(tau); d1=(math.log(S/K)+0.5*SIG*SIG*tau)/sq; d2=d1-sq
    e=math.exp(-Q*tau); er=math.exp(-R*tau)
    return S*e*N1(d1)-K*er*N1(d2) if t=='c' else K*er*N1(-d2)-S*e*N1(-d1)

def struct_delta(S,tau):
    d=-bsd('p',S,KP,tau)+bsd('c',S,K1,tau)-bsd('c',S,K2,tau)
    return min(max(d,WMIN),WMAX)
def struct_value(S,tau):
    return -bsp('p',S,KP,tau)+bsp('c',S,K1,tau)-bsp('c',S,K2,tau)
V0=struct_value(100.,T)
def struct_ret(S,tau):
    if tau is None:
        V=-max(KP-S,0)+max(S-K1,0)-max(S-K2,0)
    else:
        V=struct_value(S,tau)
    return V-V0*math.exp(R*(T-(tau if tau is not None else 0.0)))

LEVELS=[140,130,120,110,100,90,80,70,60]
TAUS=[(3.0,3/12),(2.5,2.5/12),(2.0,2/12),(1.5,1.5/12),(1.0,1/12),(0.5,0.5/12),('만기',None)]
print(f"초기(설정 시): 편입비 {struct_delta(100,T)*100:.0f}% · 순프리미엄 {V0:+.2f}% (풋 {bsp('p',100,KP,T):.2f} 수취 − 콜스프레드 {bsp('c',100,K1,T)-bsp('c',100,K2,T):.2f} 지불)")
print("\n===== 표 A. 단일 3개월 구조 — 편입비(%) =====")
hdr="지수/잔존 | "+" | ".join((str(m)+'개월' if m!='만기' else ' 만기 ') for m,_ in TAUS)
print(hdr)
for lv in LEVELS:
    row=[f"{lv:>4}"]
    for m,tau in TAUS:
        tv=(1/504 if tau is None else tau)   # 만기 편입비는 반영업일 전 기준
        row.append(f"{struct_delta(float(lv),tv)*100:5.0f}%")
    print(" | ".join(row))
print("\n===== 표 A. 단일 3개월 구조 — 예상수익률(원금 대비 %) =====")
print(hdr)
for lv in LEVELS:
    row=[f"{lv:>4}"]
    for m,tau in TAUS:
        row.append(f"{struct_ret(float(lv),tau):+6.1f}%")
    print(" | ".join(row))

print("\n===== 표 B. 3개월 리셋 방식 — 매 분기 지수 L% 변동 반복 가정, 누적 수익률(%) =====")
print("분기당 등락 | 분기(3개월) | 6개월 | 9개월 | 12개월")
for L in (30,20,10,0,-10,-20,-30):
    S=100.0*(1+L/100)
    q=struct_ret(S,None)/100
    row=[f"{L:+4d}%",f"{q*100:+7.2f}%"]
    for k in (2,3,4):
        row.append(f"{((1+q)**k-1)*100:+7.2f}%")
    print(" | ".join(row))
print(f"\n리셋 직후에는 행사가가 새 지수로 재설정되어 편입비가 지수 수준과 무관하게 초기값 {struct_delta(100,T)*100:.0f}%로 복귀합니다.")
