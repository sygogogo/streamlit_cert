import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from datetime import datetime
import textwrap
import requests
import os

# 파일 경로 설정
FONT_PATH = "./HIGothic.ttf"  # 정확한 상대경로로 지정
BG_IMAGE_PATH = "/mnt/data/가입증명서 배경 디자인.png"
PDF_OUTPUT_PATH = "/mnt/data/가입증명서.pdf"

# 폰트 등록
pdfmetrics.registerFont(TTFont("HIGothic", FONT_PATH))

# 페이지 설정
page_width, page_height = A4
margin_left = 72
max_text_width = 521 - margin_left
line_height = 16

# Streamlit UI
st.title("📄 가입증명서 자동 생성기 (with Gemini + PDF)")

# Gemini API 키 입력
api_key = st.text_input("🔐 Gemini API 키를 입력하세요", type="password")

# 사용자 입력
st.subheader("기본 정보 입력")

policy_number = st.text_input("증권번호")
insurance_period = st.text_input("보험기간")
product_name = st.text_input("보험종목")
insured = st.text_input("피보험자")
address = st.text_area("주소")

st.subheader("변동 항목")
variable_1 = st.text_input("변동항목 1 (예: 보장내용 또는 목적물 등)")
variable_2 = st.text_input("변동항목 2 (예: 금액 등)")

st.subheader("추가 항목 (선택사항)")
custom_key_1 = st.text_input("추가 항목명 1")
custom_val_1 = st.text_input("내용 1")
custom_key_2 = st.text_input("추가 항목명 2")
custom_val_2 = st.text_input("내용 2")

use_gemini = st.checkbox("🧠 Gemini로 입력 정보 요약하기")

# Gemini 요약
summary_data = None
if use_gemini and api_key and st.button("Gemini로 요약 요청"):
    prompt = f"""
    다음 정보를 가입증명서용 문장으로 요약해줘:

    증권번호: {policy_number}
    보험기간: {insurance_period}
    보험종목: {product_name}
    피보험자: {insured}
    주소: {address}
    변동항목1: {variable_1}
    변동항목2: {variable_2}
    추가항목: {custom_key_1}:{custom_val_1}, {custom_key_2}:{custom_val_2}
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        summary_data = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        st.success("요약 완료! 아래 입력창에서 확인하거나 수정하세요.")
        st.text_area("Gemini 요약 결과", summary_data, height=200)
    else:
        st.error(f"Gemini API 오류: {response.status_code}")

# PDF 생성
if st.button("📥 가입증명서 PDF 생성 및 다운로드"):
    # PDF 생성 시작
    c = canvas.Canvas(PDF_OUTPUT_PATH, pagesize=A4)
    bg = ImageReader(BG_IMAGE_PATH)
    c.drawImage(bg, 0, 0, width=page_width, height=page_height)
    c.setFont("HIGothic", 12)

    def wrap_draw(label, value, x, y_start):
        text = f"{label} : {value}"
        lines = textwrap.wrap(text, width=int(max_text_width / 7))
        for i, line in enumerate(lines):
            y = y_start - (i * line_height)
            c.drawString(x, y, line)

    # 좌표 기준점 (842 - y_px)
    positions = {
        "증권번호": 842 - 198,
        "보험기간": 842 - 226,
        "보험종목": 842 - 254,
        "피보험자": 842 - 282,
        "주소": 842 - 310,
        "변동항목1": 842 - 338,
        "변동항목2": 842 - 366,
        "추가항목1": 842 - 394,
        "추가항목2": 842 - 422,
        "가입약관": 842 - 534,
        "발행일": 842 - 562,
    }

    wrap_draw("증권번호", policy_number, margin_left, positions["증권번호"])
    wrap_draw("보험기간", insurance_period, margin_left, positions["보험기간"])
    wrap_draw("보험종목", product_name, margin_left, positions["보험종목"])
    wrap_draw("피보험자", insured, margin_left, positions["피보험자"])
    wrap_draw("주소", address, margin_left, positions["주소"])
    wrap_draw("변동항목1", variable_1, margin_left, positions["변동항목1"])
    wrap_draw("변동항목2", variable_2, margin_left, positions["변동항목2"])
    if custom_key_1 and custom_val_1:
        wrap_draw(custom_key_1, custom_val_1, margin_left, positions["추가항목1"])
    if custom_key_2 and custom_val_2:
        wrap_draw(custom_key_2, custom_val_2, margin_left, positions["추가항목2"])
    wrap_draw("가입약관", f"{product_name} 보통약관 및 특별약관", margin_left, positions["가입약관"])
    wrap_draw("발행일", datetime.today().strftime("%Y.%m.%d"), margin_left, positions["발행일"])

    c.save()

    # 다운로드 제공
    with open(PDF_OUTPUT_PATH, "rb") as f:
        st.download_button("📄 가입증명서 다운로드", f, file_name="가입증명서.pdf", mime="application/pdf")