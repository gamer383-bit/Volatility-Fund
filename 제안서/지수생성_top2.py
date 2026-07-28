# -*- coding: utf-8 -*-
"""TOP2 지수 생성 (사용자 규칙, 조건 11)
- 기준 엑셀(삼성전자_하이닉스 시트)에서 삼성전자·SK하이닉스를 50%:50%로
  '매일 리밸런싱'(비용 없음)한 지수를 생성 → 시트 우측 D열에 기록
- 지수_t = 지수_{t-1} × (1 + 0.5·r_삼성 + 0.5·r_하이닉스), 최초일=100
- 주말/휴장 채움 행은 두 종목 모두 변동 0이라 지수도 그대로 유지됨(왜곡 없음)
"""
import sys, io, os, shutil, datetime
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import openpyxl

BASE=os.path.dirname(os.path.abspath(__file__))
XLS=os.path.join(os.path.dirname(BASE),'data','삼성전자_하이닉스_코스피_코스피200_코스닥150_최근5년_주가데이터.xlsx')
BK=XLS.replace('.xlsx',f"_backup_{datetime.date.today().strftime('%Y%m%d')}.xlsx")
if not os.path.exists(BK):
    shutil.copy2(XLS,BK); print("백업:",os.path.basename(BK))

wb=openpyxl.load_workbook(XLS)
ws=wb['삼성전자_하이닉스']
# 헤더 (행 9~14 = 코드/코드명/유형/아이템코드/아이템명/집계주기)
hdr={9:'TOP2',10:'TOP2지수(삼성·하이닉스 50:50 일별리밸런싱)',11:'-',12:'-',
     13:'지수(최초일=100, 리밸비용 0)',14:'일간'}
for r,v in hdr.items(): ws.cell(row=r,column=4,value=v)

idx=None; prev_s=prev_h=None; n=0
for r in range(15,ws.max_row+1):
    s=ws.cell(row=r,column=2).value; h=ws.cell(row=r,column=3).value
    if s is None or h is None: continue
    s=float(s); h=float(h)
    if idx is None: idx=100.0
    else: idx*=1.0+0.5*(s/prev_s-1.0)+0.5*(h/prev_h-1.0)
    ws.cell(row=r,column=4,value=round(idx,6))
    prev_s,prev_h=s,h; n+=1
print(f"지수 기록: {n}행, 최종 {idx:.2f} (최초=100)")
try:
    wb.save(XLS); print("[OK] D열 저장 완료")
except PermissionError:
    print("[잠김] 엑셀에서 파일을 닫아주세요")
