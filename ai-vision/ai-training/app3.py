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
# 1. AI 파이프라인 클래스 (OpenCV 전처리 + YOLO 분석)
# =====================================================================
class SewerAIAnalyzerV2:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.DEBRIS_CLS = 0
        self.DRAIN_CLS = 1

    def preprocess_image(self, image_path):
        # 한글 경로 에러 방지를 위해 numpy로 이미지 읽기
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None: return None, None
        
        original_img = img.copy()

        # [OpenCV] CLAHE 기법으로 그림자 진 하수구 내부 밝기 개선
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        return original_img, enhanced_img

    def analyze_image(self, image_path):
        original_img, processed_img = self.preprocess_image(image_path)
        if processed_img is None:
            return {"status": "ERROR", "message": "이미지 읽기 실패"}

        # YOLO 추론 실행
        results = self.model.predict(processed_img, conf=0.25, verbose=False)
        boxes = results[0].boxes

        drain_box = None
        drain_conf = 0.0
        debris_boxes = []

        # 객체 분류
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            coords = box.xyxy[0].tolist()

            if cls == self.DRAIN_CLS:
                if conf > drain_conf:
                    drain_conf = conf
                    drain_box = coords
            elif cls == self.DEBRIS_CLS:
                debris_boxes.append((coords, conf))

        # 하수구를 못 찾은 경우
        if drain_box is None:
            return {
                "status": "UNKNOWN", "obstruction_ratio": 0.0, "confidence_score": 0.0,
                "message": "하수구 영역 미탐지", "yolo_result_img": results[0].plot()
            }

        # 막힘 비율 계산 (면적 기반)
        dr_x1, dr_y1, dr_x2, dr_y2 = drain_box
        drain_area = (dr_x2 - dr_x1) * (dr_y2 - dr_y1)
        valid_debris_area = 0.0

        for d_coords, d_conf in debris_boxes:
            d_x1, d_y1, d_x2, d_y2 = d_coords
            center_x, center_y = (d_x1 + d_x2) / 2, (d_y1 + d_y2) / 2
            if (dr_x1 <= center_x <= dr_x2) and (dr_y1 <= center_y <= dr_y2):
                valid_debris_area += (d_x2 - d_x1) * (d_y2 - d_y1)

        obstruction_ratio = min((valid_debris_area / drain_area) * 100, 100.0)

        return {
            "status": "SUCCESS",
            "obstruction_ratio": round(obstruction_ratio, 2),
            "confidence_score": round(drain_conf, 4),
            "message": "분석 완료",
            "yolo_result_img": results[0].plot(),
            "processed_img": processed_img
        }

# =====================================================================
# 2. 스트림릿(Streamlit) 웹 대시보드 UI (YOLO 단독 모드)
# =====================================================================
st.set_page_config(page_title="비전 AI 분석 대시보드", layout="wide")
st.title("👁️ 하수구 막힘 비전 AI 분석기 (YOLO 단독)")
st.markdown("업로드된 CCTV 사진을 **YOLOv8 모델**로 분석하여 하수구의 **순수 막힘 비율(%)**과 **인식 신뢰도**만 추출합니다.")

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
        
        batch_data = [] # XGBoost 연동 전, YOLO 결과만 모아둘 리스트

        # 이미지 개별 처리 루프
        for idx, file in enumerate(uploaded_files):
            # 임시 파일로 저장 (OpenCV 처리를 위함)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_path = tmp_file.name

            # AI 파이프라인 분석
            with st.spinner(f"[{file.name}] 이미지 전처리 및 YOLO 분석 중..."):
                result = analyzer.analyze_image(tmp_path)

            # 화면에 결과 렌더링 (아코디언 UI)
            with st.expander(f"결과 보기: {file.name} - 막힘 비율 {result.get('obstruction_ratio', 0)}%", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                # 1. 원본
                with col1:
                    st.caption("1. 원본 이미지")
                    st.image(Image.open(file), use_column_width=True)
                
                if result["status"] == "SUCCESS":
                    # 2. OpenCV 전처리
                    with col2:
                        st.caption("2. OpenCV 전처리 (대비 강화)")
                        st.image(cv2.cvtColor(result["processed_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                    # 3. YOLO 탐지 결과
                    with col3:
                        st.caption(f"3. YOLO 탐지 (신뢰도: {result['confidence_score']})")
                        st.image(cv2.cvtColor(result["yolo_result_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                else:
                    st.error(f"분석 실패: {result['message']}")
            
            # 임시 파일 삭제
            os.remove(tmp_path)

            # 센서 데이터 없이 순수 YOLO 분석 결과만 리스트에 추가
            batch_data.append({
                "파일명": file.name,
                "분석 상태": result.get("status", "ERROR"),
                "막힘비율(%)": result.get('obstruction_ratio', 0.0),
                "YOLO신뢰도": result.get('confidence_score', 0.0)
            })

        # =====================================================================
        # 3. 최종 YOLO 분석 데이터 출력 (XGBoost 전 단계)
        # =====================================================================
        st.markdown("---")
        st.subheader("📊 YOLO 비전 분석 결과 요약")
        st.caption("※ 아래 데이터는 향후 XGBoost 모델의 입력값(Feature)으로 활용될 수 있습니다.")

        df = pd.DataFrame(batch_data)

        # 테이블 표시
        st.dataframe(df, use_container_width=True)

        # CSV 다운로드 버튼
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 YOLO 분석 결과 CSV로 다운로드",
            data=csv_data,
            file_name="yolo_vision_results.csv",
            mime="text/csv"
        )