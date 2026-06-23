import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
import tempfile
from PIL import Image

try:
    from ultralytics import YOLO
except ImportError:
    st.error("⚠️ ultralytics 라이브러리가 필요합니다. 터미널에서 'pip install ultralytics'를 입력하세요.")

class SewerAIAnalyzerV4:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.DEBRIS_CLS = 0
        self.DRAIN_CLS = 1

    def preprocess_image(self, image_path):
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None: return None, None
        
        original_img = img.copy()

        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        return original_img, enhanced_img

    def analyze_image(self, image_path, hsv_params, shadow_thresh, variance_thresh, sat_thresh):
        original_img, processed_img = self.preprocess_image(image_path)
        if processed_img is None:
            return {"status": "ERROR", "message": "이미지 읽기 실패"}

        results = self.model.predict(processed_img, conf=0.25, verbose=False)
        boxes = results[0].boxes

        drain_box = None
        drain_conf = 0.0
        debris_boxes = []

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

        if drain_box is None:
            return {
                "status": "UNKNOWN", "total_obstruction_ratio": 0.0, "debris_ratio": 0.0, 
                "soil_ratio": 0.0, "water_ratio": 0.0, "message": "하수구 미탐지", 
                "yolo_result_img": results[0].plot(), "soil_result_img": original_img, "water_result_img": original_img
            }

        dr_x1, dr_y1, dr_x2, dr_y2 = map(int, drain_box)
        drain_area = (dr_x2 - dr_x1) * (dr_y2 - dr_y1)
        
        valid_debris_area = 0.0
        for d_coords, d_conf in debris_boxes:
            d_x1, d_y1, d_x2, d_y2 = map(int, d_coords)
            center_x, center_y = (d_x1 + d_x2) / 2, (d_y1 + d_y2) / 2
            if (dr_x1 <= center_x <= dr_x2) and (dr_y1 <= center_y <= dr_y2):
                valid_debris_area += (d_x2 - d_x1) * (d_y2 - d_y1)

        # =================================================================
        drain_crop = original_img[dr_y1:dr_y2, dr_x1:dr_x2]
        hsv_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2HSV)
        
        # --- 1. 흙 탐지 로직 (기존 동일) ---
        mask1 = cv2.inRange(hsv_crop, hsv_params['lower1'], hsv_params['upper1'])
        mask2 = cv2.inRange(hsv_crop, hsv_params['lower2'], hsv_params['upper2'])
        dirt_mask = cv2.bitwise_or(mask1, mask2)
        
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([179, 255, shadow_thresh])
        dark_hole_mask = cv2.inRange(hsv_crop, lower_dark, upper_dark)
        
        dirt_mask = cv2.bitwise_and(dirt_mask, cv2.bitwise_not(dark_hole_mask))
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dirt_mask = cv2.dilate(dirt_mask, kernel, iterations=2)
        dirt_mask = cv2.morphologyEx(dirt_mask, cv2.MORPH_OPEN, kernel)
        
        dirt_area = cv2.countNonZero(dirt_mask)
        soil_result_img = original_img.copy()
        colored_soil = np.zeros_like(drain_crop)
        colored_soil[dirt_mask > 0] = [0, 165, 255]
        cv2.addWeighted(colored_soil, 0.6, drain_crop, 1.0, 0, drain_crop)
        soil_result_img[dr_y1:dr_y2, dr_x1:dr_x2] = drain_crop

        # --- 🌟 2. [물고임 탐지 고도화] 국소 분산(Texture) + 저채도 결합 ---
        gray_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2GRAY)
        gray_f = gray_crop.astype(np.float32)

        # A. 국소 분산 계산 (표면의 거친 정도 측정)
        mu = cv2.blur(gray_f, (5, 5))
        mu_sq = mu ** 2
        sigma_sq = cv2.blur(gray_f ** 2, (5, 5)) - mu_sq
        sigma = np.sqrt(np.maximum(sigma_sq, 0))

        # 분산이 낮으면(거칠지 않으면) 매끄러운 표면으로 간주
        smooth_mask = np.zeros_like(gray_crop, dtype=np.uint8)
        smooth_mask[sigma < variance_thresh] = 255

        # B. 저채도 필터링 (물이 고여 주변 색이 사라진 상태)
        h, s, v = cv2.split(hsv_crop)
        low_sat_mask = np.zeros_like(gray_crop, dtype=np.uint8)
        low_sat_mask[s < sat_thresh] = 255

        # C. 맹점 방지: 어두운 구멍을 물로 오해하지 않도록 V 채널 하한선 부여
        water_v_mask = np.zeros_like(gray_crop, dtype=np.uint8)
        water_v_mask[v > shadow_thresh + 10] = 255 

        # A + B + C 교집합 적용
        water_mask = cv2.bitwise_and(smooth_mask, low_sat_mask)
        water_mask = cv2.bitwise_and(water_mask, water_v_mask)

        # 노이즈 정리
        ellipse_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, ellipse_kernel)
        water_mask = cv2.dilate(water_mask, ellipse_kernel, iterations=1)
        
        water_area = cv2.countNonZero(water_mask)

        water_result_img = original_img.copy()
        drain_crop_water = original_img[dr_y1:dr_y2, dr_x1:dr_x2].copy()
        colored_water = np.zeros_like(drain_crop_water)
        colored_water[water_mask > 0] = [255, 100, 0] # BGR 파란색
        cv2.addWeighted(colored_water, 0.5, drain_crop_water, 1.0, 0, drain_crop_water)
        water_result_img[dr_y1:dr_y2, dr_x1:dr_x2] = drain_crop_water
        # =================================================================

        debris_ratio = (valid_debris_area / drain_area) * 100
        soil_ratio = (dirt_area / drain_area) * 100
        water_ratio = (water_area / drain_area) * 100

        base_obstruct = (debris_ratio + soil_ratio) - ((debris_ratio * soil_ratio) / 100.0)
        total_obstruction_ratio = base_obstruct + water_ratio - ((base_obstruct * water_ratio) / 100.0)
        total_obstruction_ratio = min(total_obstruction_ratio, 100.0)

        return {
            "status": "SUCCESS",
            "total_obstruction_ratio": round(total_obstruction_ratio, 2),
            "debris_ratio": round(debris_ratio, 2),
            "soil_ratio": round(soil_ratio, 2),
            "water_ratio": round(water_ratio, 2),
            "confidence_score": round(drain_conf, 4),
            "message": "분석 완료",
            "yolo_result_img": results[0].plot(),
            "processed_img": processed_img,
            "soil_result_img": soil_result_img,
            "water_result_img": water_result_img
        }

# =====================================================================
# 2. 스트림릿(Streamlit) 웹 대시보드 UI
# =====================================================================
st.set_page_config(page_title="하수구 비전 AI", layout="wide")
st.title("👁️ 하수구 막힘 비전 AI 분석기 (질감 기반 물고임 탐지)")

st.sidebar.header("⚙️ 시스템 설정")
model_path = st.sidebar.text_input("YOLO 모델 경로", value="best.pt")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 흙 탐지(HSV) 세부 튜닝")
h1_min = st.sidebar.slider("H 하한 1", 0, 179, 10)
s1_min = st.sidebar.slider("S 하한 1", 0, 255, 40)
v1_min = st.sidebar.slider("V 하한 1", 0, 255, 20)
h1_max = st.sidebar.slider("H 상한 1", 0, 179, 35)
s1_max = st.sidebar.slider("S 상한 1", 0, 255, 255)
v1_max = st.sidebar.slider("V 상한 1", 0, 255, 200)

h2_min = st.sidebar.slider("H 하한 2", 0, 179, 0)
s2_min = st.sidebar.slider("S 하한 2", 0, 255, 20)
v2_min = st.sidebar.slider("V 하한 2", 0, 255, 10)
h2_max = st.sidebar.slider("H 상한 2", 0, 179, 10)
s2_max = st.sidebar.slider("S 상한 2", 0, 255, 200)
v2_max = st.sidebar.slider("V 상한 2", 0, 255, 150)

hsv_params = {
    'lower1': np.array([h1_min, s1_min, v1_min]), 'upper1': np.array([h1_max, s1_max, v1_max]),
    'lower2': np.array([h2_min, s2_min, v2_min]), 'upper2': np.array([h2_max, s2_max, v2_max])
}

st.sidebar.markdown("---")
st.sidebar.subheader("🕳️ 구멍 및 물고임(Texture) 탐지")
shadow_threshold = st.sidebar.slider(
    "내부 구멍 임계값 (V)", 0, 255, 45, help="이 값보다 어두우면 물이나 흙이 아닌 하수구 내부 구멍으로 봅니다."
)

# 🌟 V4 추가 슬라이더: 질감 및 채도 조절
variance_thresh = st.sidebar.slider(
    "물 표면 매끄러움 임계값 (Variance)", 
    min_value=1.0, max_value=20.0, value=7.0, step=0.5,
    help="값이 클수록 약간 거친 표면도 물로 인식합니다. (질감이 없는 밋밋한 영역 찾기)"
)
sat_thresh = st.sidebar.slider(
    "물 표면 무채색 임계값 (Saturation)", 
    min_value=10, max_value=150, value=60,
    help="값이 작을수록 완전히 색이 없는(회색/하늘색 반사) 영역만 물로 찾습니다."
)

@st.cache_resource
def load_model(path):
    if os.path.exists(path):
        return SewerAIAnalyzerV4(path)
    return None

analyzer = load_model(model_path)

if analyzer is None:
    st.sidebar.error("⚠️ 모델 파일 경로를 확인해주세요.")
else:
    uploaded_files = st.file_uploader("📸 CCTV 사진 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        batch_data = [] 
        for idx, file in enumerate(uploaded_files):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_path = tmp_file.name

            with st.spinner(f"[{file.name}] 분석 중..."):
                result = analyzer.analyze_image(tmp_path, hsv_params, shadow_threshold, variance_thresh, sat_thresh)

            with st.expander(f"결과: {file.name} (막힘 {result.get('total_obstruction_ratio', 0)}%)", expanded=True):
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.image(Image.open(file), caption="1. 원본", use_column_width=True)
                if result["status"] == "SUCCESS":
                    with col2:
                        st.image(cv2.cvtColor(result["processed_img"], cv2.COLOR_BGR2RGB), caption="2. 전처리", use_column_width=True)
                    with col3:
                        st.image(cv2.cvtColor(result["yolo_result_img"], cv2.COLOR_BGR2RGB), caption=f"3. 쓰레기 ({result['debris_ratio']}%)", use_column_width=True)
                    with col4:
                        st.image(cv2.cvtColor(result["soil_result_img"], cv2.COLOR_BGR2RGB), caption=f"4. 흙 ({result['soil_ratio']}%)", use_column_width=True)
                    with col5:
                        st.image(cv2.cvtColor(result["water_result_img"], cv2.COLOR_BGR2RGB), caption=f"5. 물고임 ({result['water_ratio']}%)", use_column_width=True)
            os.remove(tmp_path)
            batch_data.append({
                "파일명": file.name, "상태": result.get("status", "ERROR"),
                "총막힘(%)": result.get('total_obstruction_ratio', 0.0),
                "쓰레기(%)": result.get('debris_ratio', 0.0),
                "흙(%)": result.get('soil_ratio', 0.0),
                "물고임(%)": result.get('water_ratio', 0.0)
            })

        st.subheader("📊 분석 결과 요약")
        st.dataframe(pd.DataFrame(batch_data), use_container_width=True)