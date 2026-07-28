# -*- coding: utf-8 -*-
"""QPMS 별첨(성장/안정) 턴 백테스트 v2 — AI Top2 동일가중
규칙:
- 운용 시작 2021-07-28, 각 턴 지평 1년(만기 = 시작일+1년 이내 마지막 영업일)
- **운용 중 펀드 수익 +15% 도달 시 그날 종료(목표달성) → 다음 영업일 재운용**(기준가·배리어·만기 재설정)
- σ = 직전 60영업일(주말 제외) 연환산 실현변동성. 2021-07-28 직후 60일 미충족 구간은
  자료 시작부터 60일간의 변동성으로 백필(미래참조 허용, 사용자 지정)
- r=q=2.5% 고정 · 매매비용 매수 5bp/매도 30bp · 주말 포지션·수익률 변동 없음(실거래일만)
- 성장형: 참여 100%, 캡 180%, 풋100+KO60+콜스프레드110/150 (배리어 60, 턴 시작가 대비)
- 안정형: ATM 풋매도, 참여 110%, 캡 100%
데이터: xlsx(~2026-07-10 실거래일 정제) + 2026-07-13~27 Yahoo 실측(7/17 휴장, 3중 검증)
"""
import os, platform, sys, io, math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import numpy as np, pandas as pd
from scipy.special import ndtr as Nv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family']=('Malgun Gothic' if platform.system()=='Windows' else 'AppleGothic')
plt.rcParams['axes.unicode_minus']=False
NAVY='#043B72'; ORANGE='#F58220'; GRAY='#84888B'; SKY='#8fa8bf'; BLUE='#2E5F97'
BASE=os.path.dirname(os.path.abspath(__file__))
IMG=os.path.join(BASE,'img')
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')

R,Q=0.025,0.025; TCB,TCS=0.0005,0.0030
KPUT,KKO,H,K1,K2=100.,100.,60.,110.,150.
TARGET=0.15; START='2021-07-28'

def series(colidx):
    raw=pd.read_excel(XLS,sheet_name='삼성전자_하이닉스',header=None)
    d=raw.iloc[14:]
    s=pd.Series(pd.to_numeric(d.iloc[:,colidx],errors='coerce').values,
                index=pd.to_datetime(d.iloc[:,0]).values).dropna()
    idx=pd.to_datetime(s.index); s=s[idx.dayofweek<5]
    chg=s.pct_change().fillna(1.0); return s[chg!=0]
sam=series(4); hyx=series(8)
web_sam={'2026-07-13':254500,'2026-07-14':263000,'2026-07-15':279500,'2026-07-16':255000,
         '2026-07-20':244000,'2026-07-21':259000,'2026-07-22':260500,'2026-07-23':270000,
         '2026-07-24':249500,'2026-07-27':254000}
web_hyx={'2026-07-13':1845000,'2026-07-14':1913000,'2026-07-15':2082000,'2026-07-16':1842000,
         '2026-07-20':1764000,'2026-07-21':1836000,'2026-07-22':1830000,'2026-07-23':1919000,
         '2026-07-24':1759000,'2026-07-27':1816000}
sam=pd.concat([sam,pd.Series({pd.Timestamp(k):float(v) for k,v in web_sam.items()})])
hyx=pd.concat([hyx,pd.Series({pd.Timestamp(k):float(v) for k,v in web_hyx.items()})])
df=pd.concat([sam.rename('s'),hyx.rename('h')],axis=1).dropna().sort_index()
ret=(0.5*df['s'].pct_change()+0.5*df['h'].pct_change()).dropna()
dts=ret.index
print(f"Top2 시계열: {dts[0].date()} ~ {dts[-1].date()} ({len(ret)}영업일)")

# σ: 직전 60영업일 롤링(완전 60일), 초기 구간은 최초 60일 값으로 백필(미래참조 허용)
lr=np.log(1+ret)
vol60=(lr.rolling(60,min_periods=60).std()*math.sqrt(252)).bfill()

def N1(x): return float(Nv(x))
def bs_p(t,S,K,T,sig):
    sq=sig*math.sqrt(T); d1=(math.log(S/K)+(0.5*sig*sig)*T)/sq; d2=d1-sq
    e=math.exp(-Q*T); er=math.exp(-R*T)
    return S*e*N1(d1)-K*er*N1(d2) if t=='c' else K*er*N1(-d2)-S*e*N1(-d1)
def bs_d(t,S,K,T,sig):
    sq=sig*math.sqrt(T); d1=(math.log(S/K)+(0.5*sig*sig)*T)/sq
    e=math.exp(-Q*T); return e*N1(d1) if t=='c' else e*(N1(d1)-1)
def din(S,K,Hb,T,sig):
    b=R-Q; sq=sig*math.sqrt(T); mu=(b-0.5*sig*sig)/(sig*sig); phi=-1.; eta=1.
    x2=math.log(S/Hb)/sq+(1+mu)*sq; y1=math.log(Hb*Hb/(S*K))/sq+(1+mu)*sq; y2=math.log(Hb/S)/sq+(1+mu)*sq
    ebr=math.exp((b-R)*T); er=math.exp(-R*T); p1=(Hb/S)**(2*(mu+1)); p2=(Hb/S)**(2*mu)
    B=phi*S*ebr*N1(phi*x2)-phi*K*er*N1(phi*x2-phi*sq)
    C=phi*S*ebr*p1*N1(eta*y1)-phi*K*er*p2*N1(eta*y1-eta*sq)
    D=phi*S*ebr*p1*N1(eta*y2)-phi*K*er*p2*N1(eta*y2-eta*sq)
    return B-C+D
def dop(S,K,Hb,T,sig):
    if S<=Hb: return 0.0
    return max(bs_p('p',S,K,T,sig)-din(S,K,Hb,T,sig),0.0)
def ko_d(S,K,Hb,T,sig):
    if S<=Hb: return 0.0
    h=max(S*1e-4,1e-6); return (dop(S+h,K,Hb,T,sig)-dop(max(S-h,Hb+1e-9),K,Hb,T,sig))/(2*h)
def w_growth(S,tau,sig,alive):
    d=-bs_d('p',S,KPUT,tau,sig)+(ko_d(S,KKO,H,tau,sig) if alive else 0.0) \
      +bs_d('c',S,K1,tau,sig)-bs_d('c',S,K2,tau,sig)
    return min(max(d,0.0),1.8)
def w_stable(S,tau,sig):
    return min(max(-bs_d('p',S,KPUT,tau,sig),0.0)*1.10,1.0)

def simulate(kind):
    """+15% 도달 시 재운용. 반환: 턴 리스트"""
    turns=[]
    i0=int(np.searchsorted(dts,pd.Timestamp(START)))
    rday=R/252; qday=Q/252
    while i0<len(dts):
        s_dt=dts[i0]
        mat=s_dt+pd.Timedelta(days=365)
        i_end=int(np.searchsorted(dts,mat,side='right'))-1
        n=i_end-i0+1
        S=100.0; V=1.0; alive=True; touch=None; reason='만기'
        sig=max(float(vol60.iloc[max(i0-1,0)]),0.05)
        w=(w_growth(S,n/252,sig,True) if kind=='g' else w_stable(S,n/252,sig))
        pS=[S]; pV=[100.0]; pw=[w]
        j=i0
        while j<=i_end:
            r0=float(ret.iloc[j])
            V*=1.0+w*(r0+qday)+(1.0-w)*rday
            S*=1.0+r0
            if kind=='g' and alive and S<=H: alive=False; touch=dts[j]
            tau=max((i_end-j)/252,1e-8)
            sig=max(float(vol60.iloc[j]),0.05)
            nw=(w_growth(S,tau,sig,alive) if kind=='g' else w_stable(S,tau,sig))
            cost=(TCB if nw>w else TCS)*abs(nw-w)
            V-=cost*V; w=nw
            pS.append(S); pV.append(V*100); pw.append(w)
            if V>=1.0+TARGET:
                reason='목표달성'; break
            j+=1
        e_idx=min(j,i_end)
        turns.append(dict(turn=len(turns)+1,s=s_dt,e=dts[e_idx],base=S/100-1,fund=V-1,
                          pS=np.array(pS),pV=np.array(pV),pw=np.array(pw),touch=touch,reason=reason))
        i0=e_idx+1
    lt=turns[-1]
    if lt['e']==dts[-1] and lt['reason']=='만기' and (lt['s']+pd.Timedelta(days=360))>dts[-1]:
        lt['reason']='운용중'
    return turns

results={}
for kind,nm in (('g','성장형'),('s','안정형')):
    turns=simulate(kind)
    results[kind]=turns
    tot=np.prod([1+r['fund'] for r in turns])-1
    print(f"\n[{nm}] 총 {len(turns)}턴 · 누적 {tot*100:+.1f}%")
    for r in turns:
        tt=f" 배리어 {r['touch'].date()}" if r['touch'] is not None else ""
        print(f"  턴{r['turn']:2d} {r['s'].date()}~{r['e'].date()} ({len(r['pS'])-1:3d}일): 기초 {r['base']*100:+6.1f}% / 펀드 {r['fund']*100:+6.1f}% [{r['reason']}]{tt}")

# ---- 턴 요약 테이블 PNG (슬롯 비율 고정, 10턴 초과 시 2단 분할) ----
def draw_table(kind,fname,prod_label):
    rows=results[kind]; n=len(rows)
    fig,ax=plt.subplots(figsize=(7.6,3.05),dpi=150)   # 슬롯(5.0x2.03in) 비율 유지
    ax.axis('off'); fig.patch.set_facecolor('white')
    ax.add_patch(plt.Rectangle((0.005,0.01),0.99,0.98,fill=False,ec='#d5dde6',lw=1.4,
                 transform=ax.transAxes,clip_on=False))
    ax.text(0.03,0.90,'턴 요약  (목표 +15% 달성 시 재운용)',transform=ax.transAxes,fontsize=11.5,fontweight='bold',color=NAVY)
    cols=['턴','기간','기초',prod_label.replace('상품1(','').replace('상품2(','').replace(')',''),'종료']
    two=n>10
    blocks=[rows] if not two else [rows[:(n+1)//2],rows[(n+1)//2:]]
    spans=[(0.03,0.97)] if not two else [(0.03,0.50),(0.53,0.97)]
    nrow=max(len(b) for b in blocks)
    hy=0.78; dy=(hy-0.06)/(nrow+0.3)
    fs_h,fs=8.6,8.0
    for (x0,x1),blk in zip(spans,blocks):
        wsp=x1-x0
        xs=[x0, x0+0.055*wsp/0.47 if two else x0+0.06,
            x0+wsp*0.60, x0+wsp*0.78, x0+wsp*0.80]
        xs=[x0, x0+wsp*0.10, x0+wsp*0.62, x0+wsp*0.80, x0+wsp*0.82]
        for c,x in zip(cols,[xs[0],xs[1],xs[2]-wsp*0.14,xs[3]-wsp*0.13,xs[4]]):
            ax.text(x,hy,c,transform=ax.transAxes,fontsize=fs_h,fontweight='bold',color=BLUE)
        ax.plot([x0,x1],[hy-0.03,hy-0.03],transform=ax.transAxes,color='#c9d5e2',lw=1.0)
        for i,r in enumerate(blk):
            y=hy-dy*(i+1)
            end=('목표' if r['reason']=='목표달성' else ('운용중' if r['reason']=='운용중' else '만기'))+('·B' if r['touch'] is not None else '')
            vals=[str(r['turn']),f"{r['s'].strftime('%y.%m.%d')}~{r['e'].strftime('%y.%m.%d')}",
                  f"{r['base']*100:+.0f}%",f"{r['fund']*100:+.1f}%",end]
            for j,(v,x) in enumerate(zip(vals,xs)):
                ax.text(x, y, v, transform=ax.transAxes, fontsize=fs,
                        color=(NAVY if j==3 else ('#c05000' if (j==4 and '목표' in v) else '#333333')),
                        ha=('right' if j in (2,3) else 'left'), fontweight=('bold' if j==3 else 'normal'))
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight',facecolor='white'); plt.close(fig)
    print("saved",fname,f"({n}턴, {'2단' if two else '1단'})")
draw_table('g','qpms_table_g.png','상품1(성장형)')
draw_table('s','qpms_table_s.png','상품2(안정형)')

# ---- 예시 그래프: 하락기/상승기 턴 ----
def draw_turn(kind,r,fname,label,color):
    x=np.arange(len(r['pS']))
    fig,ax=plt.subplots(figsize=(7.4,3.16),dpi=150)
    ax2=ax.twinx()
    ax2.fill_between(x,r['pw']*100,color=color,alpha=0.12,lw=0)
    ax2.set_ylim(0,200); ax2.set_yticks([0,50,100,150,200])
    ax2.set_yticklabels(['0%','','100%','','200%'],fontsize=8,color=GRAY)
    ax.plot(x,r['pS'],color=SKY,lw=1.6,label='기초지수(시작=100)')
    ax.plot(x,r['pV'],color=color,lw=2.0,label='펀드 NAV')
    ax.axhline(100,color='#c9d5e2',lw=0.8)
    ax.axhline(115,color='#c05000',ls=':',lw=1.0)
    if r['touch'] is not None:
        ti=int(np.searchsorted(dts,r['touch']))-int(np.searchsorted(dts,r['s']))+1
        ax.axvline(ti,color='#D02F00',ls='--',lw=1.1)
    ax.set_title(f"{label} — 턴{r['turn']} ({r['s'].date()} ~ {r['e'].date()})  기초 {r['base']*100:+.1f}% / 펀드 {r['fund']*100:+.1f}% [{r['reason']}]",
                 fontsize=10,color=NAVY,fontweight='bold',loc='left')
    ax.set_xlabel('영업일차',fontsize=9,color=NAVY)
    ax.legend(fontsize=8.5,frameon=False,loc='upper left')
    ax.grid(alpha=0.2); ax.spines[['top']].set_visible(False)
    ax.tick_params(labelsize=9)
    fig.text(0.99,0.01,'음영=편입비(우축) · 점선=목표 +15%',ha='right',color=GRAY,fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname)
for kind,color in (('g',ORANGE),('s',NAVY)):
    rows=results[kind]
    down=min(rows,key=lambda r:r['base'])
    up=max(rows,key=lambda r:r['base'])
    draw_turn(kind,down,f'qpms_down_{kind}.png','하락기 예시',color)
    draw_turn(kind,up,  f'qpms_up_{kind}.png','상승기 예시',color)
print("done")
