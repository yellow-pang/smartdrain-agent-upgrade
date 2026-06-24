import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
import tempfile
from PIL import Image

# YOLO 라이브러리가 설치되어 있어야 합니다. (pip install ultralytics)
try:
    from ultralytics import YOLO
except ImportError:
    st.error("⚠️ ultralytics 라이브러리가 필요합니다. 터미널에서 'pip install ultralytics'를 입력하세요.")

# =====================================================================
# 1. AI 파이프라인 클래스 (투-패스 돋보기 기법 + OpenCV 보정)
# =====================================================================
class SewerAIAnalyzerV2:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.DEBRIS_CLS = 0
        self.DRAIN_CLS = 1

    def analyze_image(self, image_path):
        # 1. 이미지 로드 (한글 경로 에러 방지)
        img_array = np.fromfile(image_path, np.uint8)
        original_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if original_img is None:
            return {"status": "ERROR", "message": "이미지 읽기 실패"}

        # -------------------------------------------------------------
        # [STEP 1] 1차 훑어보기: 전체 화면에서 하수구 위치 찾기
        # -------------------------------------------------------------
        first_results = self.model.predict(original_img, conf=0.3, verbose=False)
        
        drain_box = None
        drain_conf = 0.0

        for box in first_results[0].boxes:
            if int(box.cls[0]) == self.DRAIN_CLS and float(box.conf[0]) > drain_conf:
                drain_conf = float(box.conf[0])
                drain_box = [int(v) for v in box.xyxy[0].tolist()]

        # 하수구를 아예 못 찾았을 경우
        if drain_box is None:
            return {
                "status": "UNKNOWN", "obstruction_ratio": 0.0, "confidence_score": 0.0,
                "message": "하수구 영역 미탐지", 
                "yolo_result_img": first_results[0].plot(),
                "processed_img": original_img
            }

        # -------------------------------------------------------------
        # [STEP 2] OpenCV 보정: 하수구 부분만 자르고(Crop) 대비 강화
        # -------------------------------------------------------------
        x1, y1, x2, y2 = drain_box
        h, w = original_img.shape[:2]
        
        # 하수구 주변 여백(Padding 15%)을 주고 안전하게 자릅니다
        pad_x = int((x2 - x1) * 0.15)
        pad_y = int((y2 - y1) * 0.15)
        
        cx1 = max(0, x1 - pad_x)
        cy1 = max(0, y1 - pad_y)
        cx2 = min(w, x2 + pad_x)
        cy2 = min(h, y2 + pad_y)
        
        cropped_img = original_img[cy1:cy2, cx1:cx2]

        # 크롭된 하수구 이미지에 CLAHE 보정 (그림자 제거)
        lab = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced_cropped = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # -------------------------------------------------------------
        # [STEP 3] 2차 정밀 분석: 확대 보정된 하수구 안에서 쓰레기 비율 계산
        # -------------------------------------------------------------
        second_results = self.model.predict(enhanced_cropped, conf=0.20, verbose=False)
        
        # 2차 추론에서 하수구 영역 확보 (안 잡히면 크롭된 전체 화면을 하수구로 간주)
        second_drain_area = 0
        final_dr_x1, final_dr_y1 = 0, 0
        final_dr_x2, final_dr_y2 = enhanced_cropped.shape[1], enhanced_cropped.shape[0]
        
        for box in second_results[0].boxes:
            if int(box.cls[0]) == self.DRAIN_CLS:
                fx1, fy1, fx2, fy2 = box.xyxy[0].tolist()
                area = (fx2 - fx1) * (fy2 - fy1)
                if area > second_drain_area:
                    second_drain_area = area
                    final_dr_x1, final_dr_y1, final_dr_x2, final_dr_y2 = fx1, fy1, fx2, fy2

        if second_drain_area == 0:
            second_drain_area = final_dr_x2 * final_dr_y2

        # 쓰레기(Debris) 면적 정밀 계산
        valid_debris_area = 0.0
        for box in second_results[0].boxes:
            if int(box.cls[0]) == self.DEBRIS_CLS:
                dx1, dy1, dx2, dy2 = box.xyxy[0].tolist()
                cx, cy = (dx1 + dx2) / 2, (dy1 + dy2) / 2
                
                # 쓰레기가 확대된 하수구 영역 안에 있을 때만 추가
                if (final_dr_x1 <= cx <= final_dr_x2) and (final_dr_y1 <= cy <= final_dr_y2):
                    valid_debris_area += (dx2 - dx1) * (dy2 - dy1)

        obstruction_ratio = min((valid_debris_area / second_drain_area) * 100, 100.0)

        return {
            "status": "SUCCESS",
            "obstruction_ratio": round(obstruction_ratio, 2),
            "confidence_score": round(drain_conf, 4),
            "message": "돋보기 정밀 분석 완료",
            "yolo_result_img": second_results[0].plot(),  # 확대한 곳에 박스 친 최종 결과
            "processed_img": enhanced_cropped             # OpenCV가 하수구만 오려낸 이미지
        }

# =====================================================================
# 2. 스트림릿(Streamlit) 웹 대시보드 UI
# =====================================================================
st.set_page_config(page_title="비전 AI 분석 대시보드", layout="wide")
st.title("👁️ 하수구 막힘 비전 AI 분석기 (투-패스 돋보기 적용)")
st.markdown("멀리 있는 하수구도 **AI가 스스로 찾아서 확대한 후(Crop), OpenCV로 보정하여 정밀하게** 막힘 비율을 계산합니다.")

# 사이드바 설정
st.sidebar.header("⚙️ 시스템 설정")
model_path = st.sidebar.text_input("학습된 YOLO 모델 경로 (.pt)", value="best.pt")

@st.cache_resource
def load_model(path):
    if os.path.exists(path):
        return SewerAIAnalyzerV2(path)
    return None

analyzer = load_model(model_path)

if analyzer is None:
    st.sidebar.error(f"⚠️ 모델 파일을 찾을 수 없습니다.\n경로를 확인해주세요: {model_path}")
else:
    st.sidebar.success("✅ 비전 AI 모델 로드 완료!")

    # 다중 파일 업로드
    uploaded_files = st.file_uploader("📸 CCTV 하수구 사진들을 올려주세요 (여러 장 가능)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"총 **{len(uploaded_files)}**장의 이미지가 업로드되었습니다.")
        st.markdown("---")
        
        batch_data = [] 

        # 이미지 개별 처리 루프
        for idx, file in enumerate(uploaded_files):
            # 임시 파일로 저장 
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_path = tmp_file.name

            # AI 파이프라인 분석
            with st.spinner(f"[{file.name}] 하수구 탐색 및 돋보기 분석 중..."):
                result = analyzer.analyze_image(tmp_path)

            # 화면에 결과 렌더링 (아코디언 UI)
            with st.expander(f"결과 보기: {file.name} - 막힘 비율 {result.get('obstruction_ratio', 0)}%", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.caption("1. 멀리서 찍힌 원본")
                    st.image(Image.open(file), use_column_width=True)
                
                if result["status"] == "SUCCESS":
                    with col2:
                        st.caption("2. 하수구 자동 추적 및 확대 보정 (OpenCV)")
                        st.image(cv2.cvtColor(result["processed_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                    with col3:
                        st.caption(f"3. 돋보기 정밀 탐지 (막힘: {result['obstruction_ratio']}%)")
                        st.image(cv2.cvtColor(result["yolo_result_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                else:
                    st.error(f"분석 실패: {result['message']}")
            
            # 임시 파일 삭제
            os.remove(tmp_path)

            # 데이터 추가
            batch_data.append({
                "파일명": file.name,
                "분석 상태": result.get("status", "ERROR"),
                "막힘비율(%)": result.get('obstruction_ratio', 0.0),
                "YOLO신뢰도": result.get('confidence_score', 0.0)
            })

        # =====================================================================
        # 3. 최종 분석 데이터 표 출력
        # =====================================================================
        st.markdown("---")
        st.subheader("📊 돋보기 정밀 분석 결과 요약")

        df = pd.DataFrame(batch_data)
        st.dataframe(df, use_container_width=True)

        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 정밀 분석 결과 CSV로 다운로드",
            data=csv_data,
            file_name="yolo_zoomed_results.csv",
            mime="text/csv"
        )