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

try:
    from sklearn.metrics import mean_absolute_error, accuracy_score
except ImportError:
    st.error("⚠️ scikit-learn 라이브러리가 필요합니다. 터미널에서 'pip install scikit-learn'을 입력하세요.")

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
            return {"status": "ERROR", "message": "이미지 읽기 실패", "total_obstruction_ratio": -1.0, 
                    "debris_ratio": -1.0, "soil_ratio": -1.0, "water_ratio": -1.0, "confidence_score": 0.0}

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
                "status": "UNKNOWN", "total_obstruction_ratio": -1.0, "debris_ratio": -1.0, 
                "soil_ratio": -1.0, "water_ratio": -1.0, "message": "하수구 미탐지", 
                "confidence_score": 0.0,
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

        drain_crop = original_img[dr_y1:dr_y2, dr_x1:dr_x2]
        hsv_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2HSV)
        
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

        gray_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2GRAY)
        gray_f = gray_crop.astype(np.float32)

        mu = cv2.blur(gray_f, (5, 5))
        mu_sq = mu ** 2
        sigma_sq = cv2.blur(gray_f ** 2, (5, 5)) - mu_sq
        sigma = np.sqrt(np.maximum(sigma_sq, 0))

        smooth_mask = np.zeros_like(gray_crop, dtype=np.uint8)
        smooth_mask[sigma < variance_thresh] = 255

        h, s, v = cv2.split(hsv_crop)
        low_sat_mask = np.zeros_like(gray_crop, dtype=np.uint8)
        low_sat_mask[s < sat_thresh] = 255

        water_v_mask = np.zeros_like(gray_crop, dtype=np.uint8)
        water_v_mask[v > shadow_thresh + 10] = 255 

        water_mask = cv2.bitwise_and(smooth_mask, low_sat_mask)
        water_mask = cv2.bitwise_and(water_mask, water_v_mask)

        ellipse_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, ellipse_kernel)
        water_mask = cv2.dilate(water_mask, ellipse_kernel, iterations=1)
        
        water_area = cv2.countNonZero(water_mask)

        water_result_img = original_img.copy()
        drain_crop_water = original_img[dr_y1:dr_y2, dr_x1:dr_x2].copy()
        colored_water = np.zeros_like(drain_crop_water)
        colored_water[water_mask > 0] = [255, 100, 0]
        cv2.addWeighted(colored_water, 0.5, drain_crop_water, 1.0, 0, drain_crop_water)
        water_result_img[dr_y1:dr_y2, dr_x1:dr_x2] = drain_crop_water

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

def detect_environment(image_path):
    img_array = np.fromfile(image_path, np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if image is None: return "DAY", 0.0, 0.0

    hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    _, _, v = cv2.split(hsv_img)
    
    mean_v = np.mean(v)
    
    # 야간은 명도(밝기)로 판단 유지
    if mean_v < 40.0:
        return "NIGHT", mean_v, 0.0

    height = image.shape[0]
    road_roi = image[0:int(height * 0.2), :] 
    if road_roi.size == 0: return "DAY", mean_v, 0.0

    road_gray = cv2.cvtColor(road_roi, cv2.COLOR_BGR2GRAY)
    
    # 🌟 핵심 수정: 밝기(빛 반사) 조건은 무시하고 매끄러움(분산) 조건 대폭 완화!
    road_variance = np.var(road_gray)
    
    if road_variance < 3000.0: # 800에서 3000으로 범위를 확 늘렸습니다.
        return "RAIN", mean_v, road_variance

    return "DAY", mean_v, road_variance

# =====================================================================
# 파라미터 프리셋 (🌟 우천 Variance 하향 조절)
# =====================================================================
PRESETS = {
    "DAY": {
        "hsv": {'lower1': np.array([10, 40, 20]), 'upper1': np.array([35, 255, 200]),
                'lower2': np.array([0, 20, 10]), 'upper2': np.array([10, 200, 150])},
        "shadow": 45, "variance": 7.0, "sat": 60, "icon": "☀️ 주간 맑음"
    },
    "NIGHT": {
        "hsv": {'lower1': np.array([10, 40, 10]), 'upper1': np.array([35, 255, 255]),
                'lower2': np.array([0, 20, 0]), 'upper2': np.array([10, 200, 200])},
        "shadow": 60, "variance": 12.0, "sat": 50, "icon": "🌙 야간"
    },
    "RAIN": {
        "hsv": {'lower1': np.array([10, 30, 20]), 'upper1': np.array([35, 255, 200]),
                'lower2': np.array([0, 20, 10]), 'upper2': np.array([10, 200, 150])},
        "shadow": 40, "variance": 10.0, "sat": 60, "icon": "☔ 우천 (비)" # 🌟 15.0 -> 10.0 으로 하향
    }
}

# =====================================================================
# 스트림릿 UI
# =====================================================================
st.set_page_config(page_title="하수구 비전 AI", layout="wide")
st.title("👁️ 하수구 막힘 비전 AI 통합 파이프라인")

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

st.sidebar.header("⚙️ 시스템 설정")
model_path = st.sidebar.text_input("YOLO 모델 경로", value="best.pt")

st.sidebar.markdown("---")
st.sidebar.subheader("📈 AI 성능 평가 (Ground Truth)")
gt_file = st.sidebar.file_uploader("정답 데이터(CSV) 업로드", type=["csv"])

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 환경 감지 모드")
auto_mode = st.sidebar.checkbox("🌦️ 환경 자동 감지 (추천)", value=True)

if not auto_mode:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ 수동 파라미터 튜닝")
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

    manual_hsv = {
        'lower1': np.array([h1_min, s1_min, v1_min]), 'upper1': np.array([h1_max, s1_max, v1_max]),
        'lower2': np.array([h2_min, s2_min, v2_min]), 'upper2': np.array([h2_max, s2_max, v2_max])
    }
    manual_shadow = st.sidebar.slider("내부 구멍 임계값 (V)", 0, 255, 45)
    manual_variance = st.sidebar.slider("물 표면 매끄러움 (Variance)", 1.0, 30.0, 7.0, 0.5)
    manual_sat = st.sidebar.slider("물 표면 무채색 (Saturation)", 10, 150, 60)

@st.cache_resource
def load_model(path):
    if os.path.exists(path):
        return SewerAIAnalyzerV4(path)
    return None

analyzer = load_model(model_path)

if analyzer is None:
    st.sidebar.error("⚠️ 모델 파일 경로를 확인해주세요.")
else:
    uploaded_files = st.file_uploader("📸 CCTV 사진 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"image_uploader_{st.session_state.uploader_key}")

    if uploaded_files:
        col_spacer, col_btn = st.columns([8, 2])
        with col_btn:
            if st.button("🗑️ 전체 화면 초기화", use_container_width=True):
                st.session_state.uploader_key += 1
                st.rerun()
        st.markdown("---")
        
        batch_data = [] 
        for idx, file in enumerate(uploaded_files):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_path = tmp_file.name

            env_mode, detected_v, detected_var = detect_environment(tmp_path)
            
            if auto_mode:
                active_preset = PRESETS[env_mode]
                p_hsv, p_shadow, p_variance, p_sat = active_preset["hsv"], active_preset["shadow"], active_preset["variance"], active_preset["sat"]
                env_tag = active_preset["icon"]
            else:
                p_hsv, p_shadow, p_variance, p_sat = manual_hsv, manual_shadow, manual_variance, manual_sat
                env_tag = "🛠️ 수동 튜닝"

            with st.spinner(f"[{file.name}] 분석 중..."):
                result = analyzer.analyze_image(tmp_path, p_hsv, p_shadow, p_variance, p_sat)

            with st.expander(f"결과: {file.name} (막힘 {result.get('total_obstruction_ratio', 0)}%) | {env_tag}", expanded=False):
                st.caption(f"*AI 추론: 화면밝기({detected_v:.1f}), 도로분산({detected_var:.1f})*")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1: st.image(Image.open(file), caption="1. 원본", use_column_width=True)
                if result["status"] == "SUCCESS":
                    with col2: st.image(cv2.cvtColor(result["processed_img"], cv2.COLOR_BGR2RGB), caption="2. 전처리", use_column_width=True)
                    with col3: st.image(cv2.cvtColor(result["yolo_result_img"], cv2.COLOR_BGR2RGB), caption=f"3. 쓰레기 ({result['debris_ratio']}%)", use_column_width=True)
                    with col4: st.image(cv2.cvtColor(result["soil_result_img"], cv2.COLOR_BGR2RGB), caption=f"4. 흙 ({result['soil_ratio']}%)", use_column_width=True)
                    with col5: st.image(cv2.cvtColor(result["water_result_img"], cv2.COLOR_BGR2RGB), caption=f"5. 물 ({result['water_ratio']}%)", use_column_width=True)
            os.remove(tmp_path)
            
            # 🌟 핵심: 엑셀 파일에 '화면밝기'와 '도로분산'을 저장!
            batch_data.append({
                "파일명": file.name, 
                "상태": result.get("status", "ERROR"),
                "환경": env_tag,
                "화면밝기": round(detected_v, 1),
                "도로분산": round(detected_var, 1),
                "총막힘(%)": result.get('total_obstruction_ratio', -1.0),
                "YOLO신뢰도": result.get('confidence_score', 0.0)
            })

        st.markdown("---")
        st.subheader("📊 데이터 분석 결과 요약")
        pred_df = pd.DataFrame(batch_data)
        st.dataframe(pred_df, use_container_width=True)
        
        raw_csv = pred_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 분석 결과 CSV 다운로드", data=raw_csv, file_name="raw_analysis_results.csv", mime="text/csv")

        if gt_file is not None:
            st.markdown("---")
            st.subheader("🎯 모델 평가 지표 (실제 vs 예측)")
            try:
                gt_file.seek(0)
                gt_df = pd.read_csv(gt_file)
                eval_df = pd.merge(pred_df, gt_df, on="파일명", how="inner")
                
                if not eval_df.empty:
                    valid_eval_df = eval_df[eval_df["총막힘(%)"] != -1.0].copy()
                    if not valid_eval_df.empty:
                        mae = mean_absolute_error(valid_eval_df["실제막힘(%)"], valid_eval_df["총막힘(%)"])
                        y_true_class = (valid_eval_df["실제막힘(%)"] >= 50.0).astype(int)
                        y_pred_class = (valid_eval_df["총막힘(%)"] >= 50.0).astype(int)
                        acc = accuracy_score(y_true_class, y_pred_class)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("평균 막힘 오차율 (MAE)", f"{mae:.2f}%")
                        col2.metric("위험 탐지 정확도 (Accuracy)", f"{acc * 100:.1f}%")
                        col3.metric("평가 제외", f"{len(eval_df) - len(valid_eval_df)} 건")

                        st.markdown("**🔍 상세 오차 비교표 (수치 확인용)**")
                        valid_eval_df['오차(%)'] = abs(valid_eval_df['총막힘(%)'] - valid_eval_df['실제막힘(%)']).round(2)
                        
                        # 🌟 엑셀에 화면밝기, 도로분산 컬럼 추가!
                        display_cols = ['파일명', '환경', '화면밝기', '도로분산', '실제막힘(%)', '총막힘(%)', '오차(%)', 'YOLO신뢰도']
                        if '시나리오내용' in valid_eval_df.columns:
                            display_cols.append('시나리오내용')
                            
                        display_df = valid_eval_df[display_cols]
                        st.dataframe(display_df, use_container_width=True)

                        eval_csv = display_df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📊 평가 상세 결과 CSV 다운로드", data=eval_csv, file_name="evaluation_detailed_results.csv", mime="text/csv")
            except Exception as e:
                st.error(f"⚠️ 평가 에러: {e}")