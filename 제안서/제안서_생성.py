# -*- coding: utf-8 -*-
"""변동성 매매 펀드 제안서 2종(KOSPI200 / AI Top2) 생성 — 미래에셋 형식 초안"""
import math
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------- 색상/폰트 ----------
NAVY=RGBColor(0x04,0x3B,0x72); ORANGE=RGBColor(0xF5,0x82,0x20); CYAN=RGBColor(0x00,0xA9,0xCE)
GRAY=RGBColor(0x84,0x88,0x8B); DGRAY=RGBColor(0x3A,0x3A,0x3A); LIGHT=RGBColor(0xEE,0xF2,0xF7)
WHITE=RGBColor(0xFF,0xFF,0xFF); LORANGE=RGBColor(0xF0,0xB2,0x6B); RED=RGBColor(0xD0,0x2F,0x00)
GREEN=RGBColor(0x1F,0x9E,0x6E)
FT="맑은 고딕"; FTB="맑은 고딕"
SW,SH=Inches(10.8),Inches(7.5)

# ---------- 옵션 계산 ----------
def N(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def bs(t,S,K,T,sig,r,q):
    if T<=0: return max(S-K,0) if t=='c' else max(K-S,0)
    sq=sig*math.sqrt(T); d1=(math.log(S/K)+(r-q+0.5*sig*sig)*T)/sq; d2=d1-sq
    if t=='c': return S*math.exp(-q*T)*N(d1)-K*math.exp(-r*T)*N(d2)
    return K*math.exp(-r*T)*N(-d2)-S*math.exp(-q*T)*N(-d1)
def scenario(sig):
    S0=100;T=1;r=0.03;q=0.02;putK=100;k1=110;k2=140
    pput=bs('p',S0,putK,T,sig,r,q); psp=bs('c',S0,k1,T,sig,r,q)-bs('c',S0,k2,T,sig,r,q); g=math.exp(r*T)
    rows=[]
    for m in [60,70,80,90,100,110,120,130,140,150]:
        stable=pput*g-max(putK-m,0)
        active=stable+((max(m-k1,0)-max(m-k2,0))-psp*g)
        rows.append((m,stable,active))
    return pput,psp,rows

# ---------- 그리기 헬퍼 ----------
def bg(slide,color):
    r=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,SW,SH)
    r.fill.solid(); r.fill.fore_color.rgb=color; r.line.fill.background()
    r.shadow.inherit=False
    slide.shapes._spTree.remove(r._element); slide.shapes._spTree.insert(2,r._element)
    return r
def rect(slide,x,y,w,h,color,line=None):
    r=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,x,y,w,h)
    r.fill.solid(); r.fill.fore_color.rgb=color
    if line is None: r.line.fill.background()
    else: r.line.color.rgb=line; r.line.width=Pt(0.75)
    r.shadow.inherit=False; return r
def txt(slide,x,y,w,h,runs,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,sp=1.0,wrap=True):
    tb=slide.shapes.add_textbox(x,y,w,h); tf=tb.text_frame; tf.word_wrap=wrap
    tf.margin_left=Pt(2); tf.margin_right=Pt(2); tf.margin_top=Pt(1); tf.margin_bottom=Pt(1)
    tf.vertical_anchor=anchor
    if isinstance(runs[0],tuple): runs=[runs]
    for i,para in enumerate(runs):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment=align; p.line_spacing=sp
        for (t,sz,col,b) in para:
            r=p.add_run(); r.text=t; f=r.font; f.size=Pt(sz); f.bold=b; f.color.rgb=col; f.name=FT
    return tb
def bullets(slide,x,y,w,h,items,sz=13,col=DGRAY,gap=1.15):
    tb=slide.shapes.add_textbox(x,y,w,h); tf=tb.text_frame; tf.word_wrap=True
    for i,(mark,t,c,b) in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.line_spacing=gap; p.space_after=Pt(3)
        r=p.add_run(); r.text=(mark+" " if mark else "")+t
        r.font.size=Pt(sz); r.font.color.rgb=c; r.font.bold=b; r.font.name=FT
    return tb
def footer(slide,pg,note="※ 상기 자료는 이해를 돕기 위한 예시이며 실제 투자내용을 의미하지 않습니다. 시뮬레이션은 가정에 따른 것으로 실제와 다를 수 있습니다."):
    txt(slide,Inches(0.5),Inches(7.12),Inches(8.6),Inches(0.32),[[(note,7,GRAY,False)]])
    txt(slide,Inches(9.9),Inches(7.12),Inches(0.6),Inches(0.32),[[(str(pg),9,GRAY,True)]],align=PP_ALIGN.RIGHT)
def header(slide,kicker,title):
    rect(slide,Inches(0.5),Inches(0.55),Inches(0.14),Inches(0.62),ORANGE)
    txt(slide,Inches(0.75),Inches(0.5),Inches(9),Inches(0.35),[[(kicker,12,ORANGE,True)]])
    txt(slide,Inches(0.75),Inches(0.8),Inches(9.5),Inches(0.55),[[(title,23,NAVY,True)]])

def make_table(slide,x,y,w,rows,colw,header_fill=NAVY,fs=11,hrow=True,rh=Inches(0.34)):
    nr=len(rows); nc=len(rows[0])
    gt=slide.shapes.add_table(nr,nc,x,y,w,rh*nr).table
    gt.first_row=False; gt.horz_banding=False
    # remove default style banding by setting col widths
    for j,cw in enumerate(colw): gt.columns[j].width=cw
    for i,row in enumerate(rows):
        gt.rows[i].height=rh
        for j,val in enumerate(row):
            c=gt.cell(i,j); c.margin_left=Pt(5); c.margin_right=Pt(5); c.margin_top=Pt(1); c.margin_bottom=Pt(1)
            c.vertical_anchor=MSO_ANCHOR.MIDDLE
            tf=c.text_frame; tf.word_wrap=True; p=tf.paragraphs[0]
            r=p.add_run(); r.text=str(val); r.font.name=FT; r.font.size=Pt(fs)
            if hrow and i==0:
                c.fill.solid(); c.fill.fore_color.rgb=header_fill
                r.font.color.rgb=WHITE; r.font.bold=True; p.alignment=PP_ALIGN.CENTER
            else:
                c.fill.solid(); c.fill.fore_color.rgb=(LIGHT if i%2==0 else WHITE)
                r.font.color.rgb=DGRAY; r.font.bold=(j==0)
                p.alignment=(PP_ALIGN.LEFT if j==0 else PP_ALIGN.CENTER)
    return gt

# =====================================================================
def build(path, name, under, sig, is_index):
    pput,psp,rows=scenario(sig)
    prs=Presentation(); prs.slide_width=SW; prs.slide_height=SH
    blank=prs.slide_layouts[6]
    S=lambda: prs.slides.add_slide(blank)

    # ---- 1) 표지 ----
    s=S(); bg(s,NAVY)
    rect(s,0,Inches(2.55),SW,Inches(0.06),ORANGE)
    txt(s,Inches(0.9),Inches(1.4),Inches(9),Inches(0.5),[[("미래에셋자산운용  AI금융공학운용부문",14,CYAN,True)]])
    txt(s,Inches(0.9),Inches(2.75),Inches(9.6),Inches(1.4),[
        [("변동성 매매 펀드",40,WHITE,True)],
        [(name,26,LORANGE,True)]],sp=1.05)
    txt(s,Inches(0.9),Inches(5.2),Inches(9),Inches(0.4),[[("현물 델타헤지로 옵션 페이오프를 복제하는 변동성 매매 전략",15,RGBColor(0xC9,0xD6,0xE5),False)]])
    txt(s,Inches(0.9),Inches(6.4),Inches(9),Inches(0.4),[[("2026.07  |  내부 검토용 초안",12,GRAY,False)]])
    txt(s,Inches(0.9),Inches(6.75),Inches(9.4),Inches(0.4),[[("미래에셋자산운용 컴플라이언스 검토 전 초안 — 대외 배포 금지",10,LORANGE,False)]])

    # ---- 2) 상품 개요 ----
    s=S(); bg(s,WHITE); header(s,"01  PRODUCT","상품 개요")
    ov=[["구  분","내  용"],
        ["명  칭",f"미래에셋 변동성 매매 펀드 — {name} (가칭)"],
        ["개  요","기초자산 현물 편입비를 동적으로 조절(델타헤지)하여 옵션 페이오프를 복제, 높은 변동성 프리미엄을 수취하고 상승 방향에 참여하는 전략"],
        ["기초자산",under],
        ["가정 변동성",f"연 {int(sig*100)}% (최근 실현변동성 대비 보수적 가정)"],
        ["운용 전략","ATM/OTM 옵션 페이오프의 동적 델타헤지 복제 · 최대 편입비 180% 제한"],
        ["유형 구분","안정형(ATM 풋 매도) / 적극형(풋 매도 + 콜 스프레드)"],
        ["상품 유형","국내 주식형 파생 (사모 · 일임)"],
        ["투자 등급","1등급 (매우 높은 위험) · 적극투자형"],
        ["만  기","1년 (예시) · 일별 리밸런싱"],
        ["최저가입금액","3천만원"]]
    make_table(s,Inches(0.75),Inches(1.5),Inches(9.3),ov,[Inches(1.7),Inches(7.6)],fs=11,rh=Inches(0.44))
    txt(s,Inches(0.75),Inches(6.55),Inches(9.4),Inches(0.5),[
        [("※ 원금 손실(0~100%)이 발생할 수 있으며 손실은 투자자에게 귀속됩니다. 예금자보호법 적용 대상이 아닙니다.",8.5,GRAY,False)]])
    footer(s,2)

    # ---- 3) 수익 구조 ----
    s=S(); bg(s,WHITE); header(s,"02  PAYOFF","수익 구조 — 안정형(ATM 풋 매도) 기준")
    tb=[["만기 지수","펀드 수익률","시나리오"]]
    for m,st,ac in rows:
        sc=("급락" if m<=75 else "하락" if m<95 else "보합" if m<=110 else "상승" if m<=135 else "급등")
        tb.append([f"{m}%", f"{st:+.1f}%", sc])
    make_table(s,Inches(0.75),Inches(1.55),Inches(4.7),tb,[Inches(1.5),Inches(1.9),Inches(1.3)],fs=11,rh=Inches(0.4))
    bullets(s,Inches(5.8),Inches(1.7),Inches(4.4),Inches(4),[
        ("●",f"보합·상승 시 변동성 프리미엄 {pput*math.exp(0.03):.1f}%를 전액 확보 (상단 고정)",NAVY,True),
        ("",f"기초자산이 행사가(100%) 이상에서 만기 → 최대 수익 {pput*math.exp(0.03):.1f}%",DGRAY,False),
        ("●","하락 시 행사가 이하부터 손실이 누적 (풋 매도의 본질)",RED,True),
        ("",f"예: 지수 -20% → 약 {rows[2][1]:+.1f}% (지수 80% 기준)",DGRAY,False),
        ("●","변동성이 높을수록 수취 프리미엄(=최대수익)이 커짐",ORANGE,True),
        ("●","현물 델타헤지로 복제 → 옵션 직접매도 대비 증거금·유동성 제약 없음",CYAN,True),
    ],sz=12.5,gap=1.25)
    txt(s,Inches(5.8),Inches(5.7),Inches(4.4),Inches(1),[
        [("가정: T=1년, r=3%, q=2%, σ=",10,GRAY,False),(f"{int(sig*100)}%",10,ORANGE,True),
         (". 이론 페이오프 기준이며 동적헤지 복제오차·거래비용은 별도.",10,GRAY,False)]])
    footer(s,3)

    # ---- 4) 왜 이 상품인가 ① 변동성 ----
    s=S(); bg(s,WHITE); header(s,"03  WHY NOW","왜 지금 이 상품인가 ① — 역대급 변동성")
    txt(s,Inches(0.75),Inches(1.32),Inches(9.4),Inches(0.4),[[("한국시장 변동성이 최근 5년 중 최고 수준(99%ile). 변동성이 클수록 매도 프리미엄이 커집니다.",13,DGRAY,True)]])
    vt=[["기초자산","최근 60일","5년 평균","현재 백분위"],
        ["코스피200","61.9%","18.6%","99.7%"],
        ["삼성전자","76.9%","25.3%","99.7%"],
        ["SK하이닉스","90.2%","37.3%","99.6%"],
        ["AI Top2(5:5)","79.2%","28.4%","99.7%"]]
    make_table(s,Inches(0.75),Inches(1.8),Inches(4.9),vt,[Inches(1.7),Inches(1.2),Inches(1.05),Inches(0.95)],fs=10.5,rh=Inches(0.38))
    txt(s,Inches(0.75),Inches(3.75),Inches(4.9),Inches(0.35),[[("연율화 실현변동성 · 데이터: 최근 5년 주가(2021~2026)",8.5,GRAY,False)]])
    # 레버리지 ETF 되먹임 박스
    rect(s,Inches(5.85),Inches(1.8),Inches(4.2),Inches(2.3),LIGHT)
    txt(s,Inches(6.05),Inches(1.9),Inches(3.85),Inches(2.15),[
        [("변동성을 키운 구조적 원인: 단일종목 레버리지 ETF",12.5,NAVY,True)],
        [("삼성전자·SK하이닉스 단일종목 레버리지 ETF 급증 ",10.5,DGRAY,False),("(합산 AUM 13.1조원)",10.5,ORANGE,True)],
        [("두 종목이 KOSPI200의 ",10.5,DGRAY,False),("51.5%",10.5,ORANGE,True),(" (연초 38.7%→5월)",10.5,DGRAY,False)],
        [("2배 상품이 오른 날 더 사고 내린 날 더 파는 ",10.5,DGRAY,False),("종가 순응매매(+10%일 2.6조)",10.5,NAVY,True)],
        [("→ 변동성이 변동성을 부르는 되먹임",11,ORANGE,True)]],sp=1.2)
    # 하단: 잠식 vs 수취 대비
    rect(s,Inches(0.75),Inches(4.35),Inches(9.3),Inches(2.3),RGBColor(0xF2,0xF5,0xF8))
    txt(s,Inches(0.95),Inches(4.5),Inches(8.9),Inches(0.4),[[("레버리지 ETF가 '잃는' 변동성을, 본 전략은 '수취'한다",14,NAVY,True)]])
    bullets(s,Inches(0.95),Inches(5.0),Inches(8.9),Inches(1.6),[
        ("▶",("레버리지 ETF: 고가매수·저가매도로 변동성 잠식(Volatility Decay) — 실제 KODEX SK하이닉스레버리지는 7월 5거래일 만에 −20.3%(기초 −3.2% 제자리)"),RED,False),
        ("▶",("본 전략(변동성 매도 복제): 주가↓ 비중↑(저가매수)·주가↑ 비중↓(고가매도) — 확대된 변동성을 프리미엄으로 수취"),NAVY,True),
        ("▶",("변동성 확대 = 옵션 프리미엄 확대 → 변동성 매도 전략의 기대수익 극대화 구간"),DGRAY,False),
    ],sz=11.5,gap=1.25)
    footer(s,4)

    # ---- 5) 왜 ② 하방 제한 ----
    s=S(); bg(s,WHITE); header(s,"04  WHY NOW","왜 지금 이 상품인가 ② — 제한적인 하방 위험")
    txt(s,Inches(0.75),Inches(1.45),Inches(9.4),Inches(0.5),[[("삼성전자·SK하이닉스의 실적 개선과 AI 투자 사이클이 급격한 하락을 제한합니다.",14,DGRAY,True)]])
    cards=[("실적(영업이익) 개선","HBM·메모리 업사이클과 가격 반등으로 반도체 대형주 영업이익이 구조적으로 개선. 이익 기반이 밸류에이션 하단을 지지."),
           ("AI 투자 슈퍼사이클","글로벌 AI 데이터센터·가속기 수요로 국내 메모리 2사가 핵심 수혜. 설비·R&D 투자 확대가 중장기 성장 동력."),
           ("수급·방향성","단일종목 레버리지 ETF 13.1조 유입 + 오른 날 더 사는 종가 순응매매로 상방 모멘텀 강화. 두 종목이 KOSPI200의 51.5%.")]
    x=Inches(0.75)
    for i,(t,d) in enumerate(cards):
        cx=Inches(0.75+i*3.15)
        rect(s,cx,Inches(2.2),Inches(2.95),Inches(3.0),LIGHT)
        rect(s,cx,Inches(2.2),Inches(2.95),Inches(0.55),NAVY)
        txt(s,cx+Inches(0.15),Inches(2.28),Inches(2.7),Inches(0.45),[[(t,12.5,WHITE,True)]],anchor=MSO_ANCHOR.MIDDLE)
        txt(s,cx+Inches(0.18),Inches(2.95),Inches(2.6),Inches(2.1),[[(d,11.5,DGRAY,False)]],sp=1.25)
    rect(s,Inches(0.75),Inches(5.55),Inches(9.3),Inches(1.05),RGBColor(0xFD,0xF1,0xE6))
    txt(s,Inches(1.0),Inches(5.68),Inches(8.9),Inches(0.85),[
        [("결론: ",13,ORANGE,True),("하락이 제한적이라면, ATM 풋 매도로 높은 변동성 프리미엄을 수취하는 것이 유리하다.",13,DGRAY,True)],
        [("다만 단일종목·지수 고유의 하방 위험은 상존하므로 배리어·편입비 제한 등 리스크 관리를 병행한다.",11,GRAY,False)]],sp=1.2)
    footer(s,5)

    # ---- 6) 전략 ----
    s=S(); bg(s,WHITE); header(s,"05  STRATEGY","전략 — 변동성 매도 + 방향 투자")
    txt(s,Inches(0.75),Inches(1.45),Inches(9.4),Inches(0.4),[[("변동성이 높아 프리미엄은 크고(매도 유리), 방향은 위(상승 참여)라는 두 관점을 하나의 포트폴리오에 결합.",13,DGRAY,True)]])
    boxes=[("① 변동성 매도","ATM 풋 매도 페이오프를 현물 델타헤지로 복제. 높은 변동성 프리미엄을 수취.",NAVY),
           ("② 방향 투자","콜 스프레드 매수로 상승 구간 추가 수익. 실적·AI·레버리지 수급의 상방에 베팅.",ORANGE),
           ("③ 리스크 관리","최대 편입비 180% 제한 · (옵션) 낙아웃 풋으로 급락 시 하방 완충.",CYAN)]
    for i,(t,d,c) in enumerate(boxes):
        by=Inches(2.15+i*1.35)
        rect(s,Inches(0.75),by,Inches(0.9),Inches(1.15),c)
        txt(s,Inches(0.75),by,Inches(0.9),Inches(1.15),[[(t.split()[0],20,WHITE,True)]],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)
        rect(s,Inches(1.75),by,Inches(8.3),Inches(1.15),LIGHT)
        txt(s,Inches(1.95),by+Inches(0.12),Inches(7.9),Inches(0.95),[
            [(t[2:],14,c,True)],[(d,12.5,DGRAY,False)]],sp=1.15,anchor=MSO_ANCHOR.MIDDLE)
    footer(s,6)

    # ---- 7) 유형별 구조 ----
    s=S(); bg(s,WHITE); header(s,"06  TYPES","투자 유형 — 적극형 / 안정형")
    # 안정형 표
    txt(s,Inches(0.75),Inches(1.45),Inches(4.6),Inches(0.35),[[("안정형 (변동성 안정 투자용)",14,NAVY,True)]])
    txt(s,Inches(0.75),Inches(1.8),Inches(4.6),Inches(0.3),[[("ATM 풋 매도 단독 · 프리미엄 수취",11,GRAY,False)]])
    st_t=[["만기지수","수익률"]]+[[f"{m}%",f"{st:+.1f}%"] for m,st,ac in rows]
    make_table(s,Inches(0.75),Inches(2.15),Inches(4.4),st_t,[Inches(2.2),Inches(2.2)],fs=10.5,rh=Inches(0.32),header_fill=NAVY)
    # 적극형 표
    txt(s,Inches(5.6),Inches(1.45),Inches(4.6),Inches(0.35),[[("적극형 (변동성 적극 투자용)",14,ORANGE,True)]])
    txt(s,Inches(5.6),Inches(1.8),Inches(4.6),Inches(0.3),[[("풋 매도 + 콜 스프레드 · 프리미엄+상방",11,GRAY,False)]])
    ac_t=[["만기지수","수익률"]]+[[f"{m}%",f"{ac:+.1f}%"] for m,st,ac in rows]
    make_table(s,Inches(5.6),Inches(2.15),Inches(4.4),ac_t,[Inches(2.2),Inches(2.2)],fs=10.5,rh=Inches(0.32),header_fill=ORANGE)
    footer(s,7,"※ 이론 페이오프(원금대비 %) 예시. σ="+f"{int(sig*100)}%"+", T=1년 가정. 동적헤지 복제오차·거래비용 별도. 실제와 다를 수 있습니다.")

    # ---- 8) 리스크 ----
    s=S(); bg(s,WHITE); header(s,"07  RISK","리스크 및 유의사항")
    bullets(s,Inches(0.75),Inches(1.6),Inches(9.3),Inches(5),[
        ("■","하방 손실 위험 (최대 위험요소): 풋 매도 본질상 기초자산 급락 시 손실이 누적되며 원금의 상당 부분 손실이 가능합니다.",NAVY,True),
        ("■","동적헤지 복제오차: 이산 리밸런싱·급변동·갭 하락 시 이론 페이오프와 실현손익이 크게 벌어질 수 있습니다(시뮬레이션상 이탈 사례 확인).",DGRAY,False),
        ("■","편입비 상한(180%) 효과: 배리어 근처 델타 급등 구간에서 완전복제가 제한되어 추가 오차가 발생할 수 있습니다.",DGRAY,False),
        ("■","낙아웃 리스크(적극형 옵션): 배리어 터치 시 하방보호가 소멸(델타=0)하여 이후 하락에 노출됩니다.",DGRAY,False),
        ("■",("단일종목 집중 위험(AI Top2)" if not is_index else "지수 변동 위험"),DGRAY,True) if not is_index else ("■","지수 변동·시장 위험: 시장 전반의 급락 국면에서 손실이 발생할 수 있습니다.",DGRAY,False),
        ("■","변동성 축소 위험: 시장 변동성이 가정보다 낮아지면 수취 프리미엄이 줄어 기대수익에 미달할 수 있습니다.",DGRAY,False),
    ],sz=12.5,gap=1.3)
    if not is_index:
        txt(s,Inches(1.05),Inches(4.15),Inches(9),Inches(0.4),[[("삼성전자·SK하이닉스 2종목에 집중되어 개별기업·반도체 사이클 리스크에 크게 노출됩니다.",11.5,GRAY,False)]])
    rect(s,Inches(0.75),Inches(5.55),Inches(9.3),Inches(1.05),LIGHT)
    txt(s,Inches(1.0),Inches(5.68),Inches(8.9),Inches(0.85),[
        [("본 상품은 1등급(매우 높은 위험) 상품으로 원금의 전부(0~100%) 손실이 발생할 수 있으며, 그 손실은 투자자에게 귀속됩니다.",11.5,RED,True)],
        [("투자 전 상품설명서·약관·계약권유문서를 반드시 확인하시기 바랍니다.",10.5,GRAY,False)]],sp=1.2)
    footer(s,8)

    # ---- 9) 운용부서/컴플 ----
    s=S(); bg(s,NAVY)
    rect(s,Inches(0.9),Inches(1.4),Inches(0.14),Inches(0.55),ORANGE)
    txt(s,Inches(1.15),Inches(1.4),Inches(9),Inches(0.6),[[("운용부서 및 유의사항",22,WHITE,True)]])
    txt(s,Inches(1.15),Inches(2.6),Inches(9),Inches(2),[
        [("AI금융공학운용부문 전략운용본부",15,CYAN,True)],
        [("Mission: 투자자 입장에서 장기 플러스 수익 달성",13,WHITE,False)],
        [("정량적 분석과 정성적 리서치의 균형 · One Team Approach",12,RGBColor(0xC9,0xD6,0xE5),False)],
        [("커버드콜·국내인덱스+·절대수익·구조화·Custom Mandate 등 운용",12,RGBColor(0xC9,0xD6,0xE5),False)]],sp=1.4)
    txt(s,Inches(1.15),Inches(5.3),Inches(8.9),Inches(1.6),[
        [("· 본 자료는 컴플라이언스 검토 전 내부 검토용 초안이며 대외 배포를 금합니다.",10,LORANGE,False)],
        [("· 랩/펀드 계약은 예금자보호법에 따라 보호되지 않으며, 자산가격·환율·신용 변동에 따라 원금손실(0~100%)이 발생할 수 있습니다.",10,RGBColor(0xC9,0xD6,0xE5),False)],
        [("· 상기 시뮬레이션은 가정에 의거한 예시로 수익을 보장하지 않으며 실제 결과와 다를 수 있습니다.",10,RGBColor(0xC9,0xD6,0xE5),False)]],sp=1.3)
    footer(s,9,"")

    prs.save(path)
    print("saved:",path)

base="C:/Users/gamer38/Documents/Claude/Projects/변동성펀드/제안서/"
build(base+"변동성매매펀드_KOSPI200_초안.pptx","KOSPI200","코스피200 지수",0.50,True)
build(base+"변동성매매펀드_AITop2_초안.pptx","AI Top2 (삼성전자·SK하이닉스)","AI Top2 — 삼성전자·SK하이닉스 (동일가중)",0.60,False)
print("done")
