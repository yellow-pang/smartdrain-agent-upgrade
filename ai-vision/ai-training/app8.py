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

# =====================================================================
# 1. AI 파이프라인 클래스 (YOLO + OpenCV 흙 탐지 + 물고임 탐지 하이브리드)
# =====================================================================
class SewerAIAnalyzerV2:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.DEBRIS_CLS = 0
        self.DRAIN_CLS = 1

    def preprocess_image(self, image_path):
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

    # 💡 water_thresh 인자 추가 (물고임 반사광 기준값)
    def analyze_image(self, image_path, hsv_params, shadow_thresh, water_thresh):
        original_img, processed_img = self.preprocess_image(image_path)
        if processed_img is None:
            return {"status": "ERROR", "message": "이미지 읽기 실패"}

        # YOLO 추론 실행
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
                "soil_ratio": 0.0, "water_ratio": 0.0,
                "confidence_score": 0.0, "message": "하수구 영역 미탐지", 
                "yolo_result_img": results[0].plot(), "soil_result_img": original_img,
                "water_result_img": original_img
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
        # 💡 [OpenCV 탐지 알고리즘] 하수구 내부 크롭
        # =================================================================
        drain_crop = original_img[dr_y1:dr_y2, dr_x1:dr_x2]
        hsv_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2HSV)
        
        # --- 1. 흙 탐지 로직 (기존 유지) ---
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
        colored_soil[dirt_mask > 0] = [0, 165, 255] # 주황색
        cv2.addWeighted(colored_soil, 0.6, drain_crop, 1.0, 0, drain_crop)
        soil_result_img[dr_y1:dr_y2, dr_x1:dr_x2] = drain_crop

        # --- 🌟 2. [물고임 탐지 추가] 엣지 소실 + 반사광 교집합 ---
        # A. 엣지 소실: 물이 고여서 거친 표면이 안보이는 밋밋한 곳 찾기
        gray_crop = cv2.cvtColor(original_img[dr_y1:dr_y2, dr_x1:dr_x2], cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_crop, 50, 150)
        no_edge_mask = cv2.bitwise_not(edges) # 엣지가 없는 곳이 흰색(255)
        
        # B. 반사광: 물 표면에 빛이 반사되어 명도(V)가 매우 높은 곳 찾기
        lower_glare = np.array([0, 0, water_thresh])
        upper_glare = np.array([179, 255, 255])
        glare_mask = cv2.inRange(hsv_crop, lower_glare, upper_glare)
        
        # C. 교집합: 밋밋하면서(no_edge) + 빛이 반사되는(glare) 영역
        water_mask = cv2.bitwise_and(no_edge_mask, glare_mask)
        
        # 노이즈 제거
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)
        water_area = cv2.countNonZero(water_mask)

        # 물고임 시각화 (파란색 하이라이팅)
        water_result_img = original_img.copy()
        drain_crop_water = original_img[dr_y1:dr_y2, dr_x1:dr_x2].copy()
        colored_water = np.zeros_like(drain_crop_water)
        colored_water[water_mask > 0] = [255, 100, 0] # 파란색 (BGR)
        cv2.addWeighted(colored_water, 0.5, drain_crop_water, 1.0, 0, drain_crop_water)
        water_result_img[dr_y1:dr_y2, dr_x1:dr_x2] = drain_crop_water

        # =================================================================
        
        debris_ratio = (valid_debris_area / drain_area) * 100
        soil_ratio = (dirt_area / drain_area) * 100
        water_ratio = (water_area / drain_area) * 100

        # 💡 3중 확률적 결합 방식 (쓰레기 + 흙 + 물)
        base_obstruct = (debris_ratio + soil_ratio) - ((debris_ratio * soil_ratio) / 100.0)
        total_obstruction_ratio = base_obstruct + water_ratio - ((base_obstruct * water_ratio) / 100.0)

        # 제한 초과 방지
        total_obstruction_ratio = min(total_obstruction_ratio, 100.0)

        return {
            "status": "SUCCESS",
            "total_obstruction_ratio": round(total_obstruction_ratio, 2),
            "debris_ratio": round(debris_ratio, 2),
            "soil_ratio": round(soil_ratio, 2),
            "water_ratio": round(water_ratio, 2), # 반환값에 물 비율 추가
            "confidence_score": round(drain_conf, 4),
            "message": "분석 완료",
            "yolo_result_img": results[0].plot(),
            "processed_img": processed_img,
            "soil_result_img": soil_result_img,
            "water_result_img": water_result_img # 시각화 이미지 추가
        }

# =====================================================================
# 2. 스트림릿(Streamlit) 웹 대시보드 UI
# =====================================================================
st.set_page_config(page_title="비전 AI 분석 대시보드", layout="wide")
st.title("👁️ 하수구 막힘 비전 AI 분석기 (흙 + 물고임 탐지)")
st.markdown("하수구 **안쪽 구멍(음영)**을 필터링하고, **물고임(침수)** 현상까지 종합적으로 감지합니다.")

st.sidebar.header("⚙️ 시스템 설정")
model_path = st.sidebar.text_input("학습된 YOLO 모델 경로 (.pt)", value="best.pt")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 흙 탐지(HSV) 세부 튜닝")

st.sidebar.markdown("**[범위 1: 황토/일반 흙]**")
h1_min = st.sidebar.slider("H 하한 1", 0, 179, 10)
s1_min = st.sidebar.slider("S 하한 1", 0, 255, 40)
v1_min = st.sidebar.slider("V 하한 1", 0, 255, 20)
h1_max = st.sidebar.slider("H 상한 1", 0, 179, 35)
s1_max = st.sidebar.slider("S 상한 1", 0, 255, 255)
v1_max = st.sidebar.slider("V 상한 1", 0, 255, 200)

st.sidebar.markdown("**[범위 2: 어두운/붉은 흙]**")
h2_min = st.sidebar.slider("H 하한 2", 0, 179, 0)
s2_min = st.sidebar.slider("S 하한 2", 0, 255, 20)
v2_min = st.sidebar.slider("V 하한 2", 0, 255, 10)
h2_max = st.sidebar.slider("H 상한 2", 0, 179, 10)
s2_max = st.sidebar.slider("S 상한 2", 0, 255, 200)
v2_max = st.sidebar.slider("V 상한 2", 0, 255, 150)

hsv_params = {
    'lower1': np.array([h1_min, s1_min, v1_min]),
    'upper1': np.array([h1_max, s1_max, v1_max]),
    'lower2': np.array([h2_min, s2_min, v2_min]),
    'upper2': np.array([h2_max, s2_max, v2_max])
}

st.sidebar.markdown("---")
st.sidebar.subheader("🕳️ 필터링 및 환경 조건")
shadow_threshold = st.sidebar.slider(
    "내부 구멍 제거 임계값 (명도 V)", 
    min_value=0, max_value=255, value=45,
    help="이 값보다 어두운 영역(하수구 안쪽 구멍)은 흙 탐지 대상에서 제외합니다."
)

# 🌟 [사이드바 물고임 튜닝 추가]
water_threshold = st.sidebar.slider(
    "물 반사광 탐지 임계값 (명도 V)", 
    min_value=150, max_value=255, value=210,
    help="비가 와서 물이 고였을 때 빛이 반사되는 밝은 영역을 탐지하는 기준값입니다."
)

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

    uploaded_files = st.file_uploader("📸 CCTV 하수구 사진들을 올려주세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"총 **{len(uploaded_files)}**장의 이미지가 업로드되었습니다.")
        st.markdown("---")
        
        batch_data = [] 

        for idx, file in enumerate(uploaded_files):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_path = tmp_file.name

            with st.spinner(f"[{file.name}] 이미지 분석 중..."):
                # 💡 water_threshold 변수 함께 전달
                result = analyzer.analyze_image(tmp_path, hsv_params, shadow_threshold, water_threshold)

            with st.expander(f"결과 보기: {file.name} - 총 막힘 비율 {result.get('total_obstruction_ratio', 0)}%", expanded=True):
                # 🌟 화면에 시각화할 이미지가 늘어났으므로 5개 열로 분할
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.caption("1. 원본 이미지")
                    st.image(Image.open(file), use_column_width=True)
                
                if result["status"] == "SUCCESS":
                    with col2:
                        st.caption("2. 전처리 (CLAHE)")
                        st.image(cv2.cvtColor(result["processed_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                    with col3:
                        st.caption(f"3. 쓰레기 (YOLO: {result['debris_ratio']}%)")
                        st.image(cv2.cvtColor(result["yolo_result_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                    with col4:
                        st.caption(f"4. 흙 (OpenCV: {result['soil_ratio']}%)")
                        st.image(cv2.cvtColor(result["soil_result_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                    with col5:
                        st.caption(f"5. 물고임 (OpenCV: {result['water_ratio']}%)")
                        st.image(cv2.cvtColor(result["water_result_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                else:
                    st.error(f"분석 실패: {result['message']}")
            
            os.remove(tmp_path)

            batch_data.append({
                "파일명": file.name,
                "분석 상태": result.get("status", "ERROR"),
                "총 막힘비율(%)": result.get('total_obstruction_ratio', 0.0),
                "쓰레기비율(%)": result.get('debris_ratio', 0.0),
                "흙비율(%)": result.get('soil_ratio', 0.0),
                "물고임비율(%)": result.get('water_ratio', 0.0), # 데이터 테이블에도 추가
                "YOLO신뢰도": result.get('confidence_score', 0.0)
            })

        st.markdown("---")
        st.subheader("📊 분석 결과 요약")
        df = pd.DataFrame(batch_data)
        st.dataframe(df, use_container_width=True)