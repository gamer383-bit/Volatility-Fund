# -*- coding: utf-8 -*-
"""QPMS 별첨(성장/안정) 턴 백테스트 v2 — AI Top2 동일가중
규칙:
- 운용 시작 2021-07-28, 각 턴 지평 1년(만기 = 시작일+1년 이내 마지막 영업일)
- **운용 중 펀드 수익 +15% 도달 시 그날 종료(목표달성) → 다음 영업일 재운용**(기준가·배리어·만기 재설정)
- σ = 직전 60영업일(주말 제외) 연환산 실현변동성. 2021-07-28 직후 60일 미충족 구간은
  자료 시작부터 60일간의 변동성으로 백필(미래참조 허용, 사용자 지정)
- r=q=2.5% 고정 · 매매비용 매수 5bp/매도 30bp · 주말 포지션·수익률 변동 없음(실거래일만)
- σ 상한 60% (60% 초과 시 60% 사용, 성장형·안정형 공통)
- 성장형: 3개 옵션 복제비율 100%, 최대 편입비 180%, 풋100+KO60+콜스프레드110/140
- 안정형: ATM 풋매도 복제비율 110%, 최대 편입비 100%
데이터: 기준 엑셀 D열 = 삼성전자·SK하이닉스 50:50 일별리밸런싱 지수(리밸비용 0, 지수생성_top2.py)
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
KPUT,KKO,H,K1,K2=100.,100.,60.,110.,140.
TARGET=0.15; START='2021-07-28'; SIGCAP=0.60; WMIN=0.10   # 최저 편입비 10% (사용자 규칙)

def load_top2():
    """엑셀 D열(지수생성_top2.py로 생성한 삼성·하이닉스 50:50 일별리밸 지수)을
    유일한 기초지수로 사용. 주말·휴장 채움(변동 0) 행 제거."""
    raw=pd.read_excel(XLS,sheet_name='삼성전자_하이닉스',header=None)
    d=raw.iloc[14:]
    s=pd.Series(pd.to_numeric(d.iloc[:,3],errors='coerce').values,
                index=pd.to_datetime(d.iloc[:,0]).values).dropna()
    idx=pd.to_datetime(s.index); s=s[idx.dayofweek<5]
    chg=s.pct_change().fillna(1.0); return s[chg!=0]
top2=load_top2()
ret=top2.pct_change().dropna()
dts=ret.index
print(f"Top2 지수(50:50 일별리밸, 엑셀 D열): {dts[0].date()} ~ {dts[-1].date()} ({len(ret)}영업일)")

# σ: 직전 60영업일 롤링(완전 60일), 초기 구간은 최초 60일 값으로 백필(미래참조 허용)
# 사용자 규칙: 변동성 60% 초과 시 60%로 상한 (성장형·안정형 공통)
lr=np.log(1+ret)
vol60=(lr.rolling(60,min_periods=60).std()*math.sqrt(252)).bfill().clip(upper=SIGCAP)

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
    return min(max(d,WMIN),1.8)          # 편입비 [최저 10%, 180%]
def w_stable(S,tau,sig):
    return min(max(-bs_d('p',S,KPUT,tau,sig)*1.10,WMIN),1.0)   # 편입비 [최저 10%, 100%]

def simulate(kind):
    """청산·재세팅 규칙(사용자 지정):
    - +15% 달성/만기일 D 종가에 전량 청산(매도 30bp) 후 같은 종가로 즉시 재세팅:
      기준가·행사가·배리어·만기(1년) 재설정, 재매수(5bp) → D+1 수익률부터 새 턴 노출
    - σ는 매일 직전 60영업일 연환산으로 갱신, r=q=2.5%
    - 회계: 주식 편입분=주가수익률, 잔여분=현금성 연 2.5%"""
    turns=[]
    G={'d':[],'V':[],'w':[],'ev':[]}                    # 연속 시계열(1년 윈도우 차트용)
    rday=R/252
    a=int(np.searchsorted(dts,pd.Timestamp(START)))     # 최초 앵커: 2021-07-28 종가 세팅(다음날부터 노출)
    V_cont=1.0
    first_anchor=True
    while a+1<len(dts):
        mat=dts[a]+pd.Timedelta(days=365)
        i_mat=int(np.searchsorted(dts,mat,side='right'))-1
        n=i_mat-a
        if n<=0: break
        S=100.0; alive=True; touch=None; reason='만기'
        sig=max(float(vol60.iloc[a]),0.05)
        tau0=(mat-dts[a]).days/365.0         # 잔존만기는 달력 기준(데이터 끝에 잘리지 않음)
        w=(w_growth(S,tau0,sig,True) if kind=='g' else w_stable(S,tau0,sig))
        V_cont*=1.0-TCB*w                    # 앵커일 종가 재매수 비용
        turnV0=V_cont
        if first_anchor:
            G['d'].append(dts[a]); G['V'].append(V_cont); G['w'].append(w)
            first_anchor=False
        elif G['d'] and G['d'][-1]==dts[a]:  # 재세팅일: 청산·재매수 비용 반영 + 새 편입비로 갱신
            G['V'][-1]=V_cont; G['w'][-1]=w
        pS=[S]; pV=[100.0]; pw=[w]
        j=a+1; hit=False
        while j<=i_mat and j<len(dts):
            r0=float(ret.iloc[j])
            V_cont*=1.0+w*r0+(1.0-w)*rday    # 주식분=주가수익률, 잔여분=현금 2.5%/년
            S*=1.0+r0
            if kind=='g' and alive and S<=H: alive=False; touch=dts[j]
            if V_cont/turnV0>=1.0+TARGET:    # 달성 당일: 리밸 없이 종가 청산으로 직행
                pS.append(S); pV.append(V_cont/turnV0*100); pw.append(w)
                G['d'].append(dts[j]); G['V'].append(V_cont); G['w'].append(w)
                hit=True; reason='목표달성'; break
            tau=max((mat-dts[j]).days/365.0,1e-8)
            sig=max(float(vol60.iloc[j]),0.05)
            nw=(w_growth(S,tau,sig,alive) if kind=='g' else w_stable(S,tau,sig))
            V_cont*=1.0-(TCB if nw>w else TCS)*abs(nw-w)
            w=nw
            pS.append(S); pV.append(V_cont/turnV0*100); pw.append(w)
            G['d'].append(dts[j]); G['V'].append(V_cont); G['w'].append(w)
            j+=1
        e_idx=min(j,i_mat,len(dts)-1)
        ongoing=(not hit) and (e_idx==len(dts)-1) and (i_mat>len(dts)-1 or (dts[a]+pd.Timedelta(days=360))>dts[-1])
        if ongoing: reason='운용중'
        if not ongoing:
            V_cont*=1.0-TCS*w                # 종료일 종가 전량 청산 비용
        turns.append(dict(turn=len(turns)+1,s=dts[a],e=dts[e_idx],base=S/100-1,
                          fund=V_cont/turnV0-1,pS=np.array(pS),pV=np.array(pV),pw=np.array(pw),
                          touch=touch,reason=reason))
        if not ongoing: G['ev'].append((dts[e_idx],reason))
        if ongoing: break
        a=e_idx                              # 다음 앵커 = 종료 당일(같은 종가로 재세팅, 익일부터 노출)
    return turns,G

results={}; gseries={}
for kind,nm in (('g','성장형'),('s','안정형')):
    turns,G=simulate(kind)
    results[kind]=turns; gseries[kind]=G
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

# ---- 예시 그래프: 하락/상승/보합 1년 구간을 '신규 설정'해서 운용 (사용자 규칙) ----
# 1) 기초지수 1년(달력) 수익률 기준으로 하락(최저)·상승(최고)·보합(|수익률| 최소) 구간 선정
# 2) 각 구간 시작일 종가를 기준가 100으로 신규 설정 → 18페이지와 동일 규칙으로 운용
#    (+15% 달성 시 당일 종가 청산 후 같은 종가로 만기 1년 재세팅·재운용)
import matplotlib.dates as mdates
px=(1.0+ret).cumprod()                      # dts 기준 누적 지수 (앵커 종가 비교용)

def pick_windows():
    worst=(None,np.inf); best=(None,-np.inf); flat=(None,np.inf)
    for i in range(len(dts)):
        t1=dts[i]+pd.Timedelta(days=365)
        if t1>dts[-1]: break
        j=int(np.searchsorted(dts,t1,side='right'))-1
        r1=float(px.iloc[j]/px.iloc[i]-1)
        if r1<worst[1]: worst=(i,r1)
        if r1>best[1]:  best=(i,r1)
        if abs(r1)<abs(flat[1]): flat=(i,r1)
    return worst,best,flat

def run_window(kind,ia):
    """구간 신규 설정 운용: 기준가=dts[ia] 종가(=100), 노출 ia+1 ~ 앵커+365일.
    +15% 달성 시 당일 종가 전량 청산(30bp) 후 같은 종가로 만기 1년 재세팅(5bp)."""
    rday=R/252
    ie=int(np.searchsorted(dts,dts[ia]+pd.Timedelta(days=365),side='right'))-1
    S=100.; V=1.; alive=True; Sb=100.
    sig=max(float(vol60.iloc[ia]),0.05)
    mat=dts[ia]+pd.Timedelta(days=365)
    w=(w_growth(S,1.0,sig,True) if kind=='g' else w_stable(S,1.0,sig))
    V*=1.0-TCB*w; turnV0=V
    dates=[dts[ia]]; pV=[100.]; pw=[w]; base=[100.]; restarts=[]
    for j in range(ia+1,ie+1):
        r0=float(ret.iloc[j]); sig=max(float(vol60.iloc[j]),0.05)
        V*=1.0+w*r0+(1.0-w)*rday
        S*=1.0+r0; Sb*=1.0+r0
        if kind=='g' and alive and S<=H: alive=False
        if V/turnV0>=1.0+TARGET and j<ie:
            restarts.append(dts[j]); V*=1.0-TCS*w
            S=100.; alive=True; mat=dts[j]+pd.Timedelta(days=365)
            nw=(w_growth(S,1.0,sig,True) if kind=='g' else w_stable(S,1.0,sig))
            V*=1.0-TCB*nw; w=nw; turnV0=V
        else:
            tau=max((mat-dts[j]).days/365.0,1e-8)
            nw=(w_growth(S,tau,sig,alive) if kind=='g' else w_stable(S,tau,sig))
            V*=1.0-(TCB if nw>w else TCS)*abs(nw-w); w=nw
        dates.append(dts[j]); pV.append(V*100); pw.append(w); base.append(Sb)
    return pd.to_datetime(dates),np.array(base),np.array(pV),np.array(pw),restarts

def draw_win(kind,color,ia,label,fname,legend=False):
    x,base,pV,pw,restarts=run_window(kind,ia)
    fig,ax=plt.subplots(figsize=(7.4,2.05),dpi=150)
    ax2=ax.twinx()
    ax2.fill_between(x,pw*100,color=color,alpha=0.13,lw=0)
    ax2.set_ylim(0,200); ax2.set_yticks([0,100,200])
    ax2.set_yticklabels(['0%','100%','200%'],fontsize=7.5,color=GRAY)
    ax.plot(x,base,color=SKY,lw=1.5,label='기초지수(시작=100)')
    ax.plot(x,pV,color=color,lw=1.9,label='펀드 NAV')
    ax.axhline(100,color='#c9d5e2',lw=0.8)
    for rd in restarts:
        ax.axvline(rd,color='#c05000',ls=':',lw=0.9,alpha=0.8)
        k=int(x.searchsorted(rd))
        if k<len(pV): ax.plot([rd],[pV[k]],marker='*',ms=9,color='#c05000',mec='white',mew=0.6,zorder=6)
    b1=float(base[-1]-100); f1=float(pV[-1]-100)
    ax.set_title(f"{label} ({x[0].strftime('%y.%m.%d')}~{x[-1].strftime('%y.%m.%d')} 신규 설정)  "
                 f"기초 {b1:+.1f}% / 펀드 {f1:+.1f}%"+(f" · 달성 {len(restarts)}회" if restarts else ""),
                 fontsize=10,color=NAVY,fontweight='bold',loc='left')
    if legend: ax.legend(fontsize=8,frameon=False,loc='best')
    ax.grid(alpha=0.2); ax.spines[['top']].set_visible(False)
    ax.tick_params(labelsize=8.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y.%m'))
    fig.tight_layout(pad=0.5)
    fig.savefig(os.path.join(IMG,fname),bbox_inches='tight'); plt.close(fig)
    print("saved",fname,f"기초 {b1:+.1f}% 펀드 {f1:+.1f}% 달성 {len(restarts)}회")

(wd_i,wd_r),(up_i,up_r),(fl_i,fl_r)=pick_windows()
print(f"\n구간 선정(1년): 하락 {dts[wd_i].date()} ({wd_r*100:+.1f}%) · 상승 {dts[up_i].date()} ({up_r*100:+.1f}%) · 보합 {dts[fl_i].date()} ({fl_r*100:+.1f}%)")
for kind,color in (('g',ORANGE),('s',NAVY)):
    draw_win(kind,color,wd_i,'하락 1년',f'qpms_down_{kind}.png',legend=True)
    draw_win(kind,color,up_i,'상승 1년',f'qpms_up_{kind}.png')
    draw_win(kind,color,fl_i,'보합 1년',f'qpms_flat_{kind}.png')
print("done")
