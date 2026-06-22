import streamlit as st
import cv2
import numpy as np
import pandas as pd
import random
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
# 2. 스트림릿(Streamlit) 웹 대시보드 UI
# =====================================================================
st.set_page_config(page_title="지능형 침수 관리 시스템", layout="wide")
st.title("🌊 지능형 침수 관리 시스템 (V2 데모)")
st.markdown("YOLOv8(시각) + 센서 데이터(수위/강수량) 통합 $\\rightarrow$ **XGBoost 물넘침 위험도 예측**")

# 사이드바 설정
st.sidebar.header("⚙️ 시스템 설정")
# 사용자가 실제로 가지고 있는 best.pt 경로를 입력할 수 있게 함
model_path = st.sidebar.text_input("학습된 YOLO 모델 경로 (.pt)", value="runs/detect/sewer_model_v2/weights/best.pt")

@st.cache_resource
def load_model(path):
    if os.path.exists(path):
        return SewerAIAnalyzerV2(path)
    return None

analyzer = load_model(model_path)

if analyzer is None:
    st.sidebar.error(f"⚠️ 모델 파일을 찾을 수 없습니다.\n경로를 확인해주세요: {model_path}")
    st.warning("👈 왼쪽 사이드바에 'best.pt' 파일의 정확한 경로를 입력해주세요.")
else:
    st.sidebar.success("✅ V2 모델 로드 완료!")

    # 다중 파일 업로드
    uploaded_files = st.file_uploader("📸 CCTV 하수구 사진들을 올려주세요 (여러 장 가능)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"총 **{len(uploaded_files)}**장의 이미지가 업로드되었습니다.")
        st.markdown("---")
        
        batch_data = [] # XGBoost로 넘길 데이터를 모아둘 리스트

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

            # 가상의 센서 데이터 생성 (실제 배포 시에는 IoT 센서 연동)
            water_level = round(random.uniform(0.0, 1.0), 2)
            rainfall = round(random.uniform(0.0, 40.0), 1)
            
            # 최종 데이터를 리스트에 추가
            batch_data.append({
                "파일명": file.name,
                "막힘비율(%)": result.get('obstruction_ratio', 0.0),
                "수위(m)": water_level,
                "강수량(mm)": rainfall,
                "YOLO신뢰도": result.get('confidence_score', 0.0)
            })

        # =====================================================================
        # 3. XGBoost 예측 시뮬레이션 및 데이터 프레임 출력
        # =====================================================================
        st.markdown("---")
        st.subheader("📊 최종 상황 판단 및 데이터 통합 (XGBoost 시뮬레이션)")

        df = pd.DataFrame(batch_data)

        # [XGBoost 판단 로직 시뮬레이션]
        def predict_risk(row):
            if row['수위(m)'] >= 0.8 or (row['수위(m)'] >= 0.6 and row['강수량(mm)'] >= 20.0):
                return "🔴 침수 발생(위험)"
            elif row['막힘비율(%)'] >= 50.0 and row['수위(m)'] >= 0.4:
                return "🟠 물넘침 임박"
            elif row['막힘비율(%)'] >= 50.0:
                return "🟡 청소 필요"
            else:
                return "🟢 정상"

        df['AI 판별 결과'] = df.apply(predict_risk, axis=1)

        # 테이블 표시
        st.dataframe(df, use_container_width=True)

        # CSV 다운로드 버튼
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 이 표를 CSV로 다운로드 (XGBoost 학습용/보고용)",
            data=csv_data,
            file_name="sewer_analysis_results.csv",
            mime="text/csv"
        )