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
# 1. AI 파이프라인 클래스 (YOLO + OpenCV 흙 탐지 하이브리드)
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
                "status": "UNKNOWN", "total_obstruction_ratio": 0.0, "debris_ratio": 0.0, "soil_ratio": 0.0,
                "confidence_score": 0.0, "message": "하수구 영역 미탐지", 
                "yolo_result_img": results[0].plot(), "soil_result_img": original_img
            }

        dr_x1, dr_y1, dr_x2, dr_y2 = map(int, drain_box)
        drain_area = (dr_x2 - dr_x1) * (dr_y2 - dr_y1)
        
        # 1. 쓰레기 면적 계산
        valid_debris_area = 0.0
        for d_coords, d_conf in debris_boxes:
            d_x1, d_y1, d_x2, d_y2 = map(int, d_coords)
            center_x, center_y = (d_x1 + d_x2) / 2, (d_y1 + d_y2) / 2
            if (dr_x1 <= center_x <= dr_x2) and (dr_y1 <= center_y <= dr_y2):
                valid_debris_area += (d_x2 - d_x1) * (d_y2 - d_y1)

        # =================================================================
        # 💡 [핵심 추가 부분] OpenCV 흙(퇴적물) 색상 기반 탐지
        # =================================================================
        # 하수구 영역만 잘라내기
        drain_crop = original_img[dr_y1:dr_y2, dr_x1:dr_x2]
        
        # BGR을 HSV 색공간으로 변환
        hsv_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2HSV)
        
        # =================================================================
        # 1. 흙 색상 범위 1 (기존 범위: 황토색/노란 흙)
        lower_brown1 = np.array([10, 40, 20])
        upper_brown1 = np.array([35, 255, 200])
        mask1 = cv2.inRange(hsv_crop, lower_brown1, upper_brown1)
        
        # 2. 흙 색상 범위 2 (추가 범위: 어둡거나 붉은 기가 도는 흙)
        lower_brown2 = np.array([0, 20, 10])    
        upper_brown2 = np.array([10, 200, 150]) 
        mask2 = cv2.inRange(hsv_crop, lower_brown2, upper_brown2)
        
        # 3. 두 범위를 합칩니다 (OR 연산)
        dirt_mask = cv2.bitwise_or(mask1, mask2)
        
        # =================================================================
        
        # 흙 면적 계산 (흰색 픽셀의 개수)
        dirt_area = cv2.countNonZero(dirt_mask)
        
        # 화면 출력을 위해 원본 이미지 복사 후, 흙 부분을 '주황색'으로 강조
        soil_result_img = original_img.copy()
        colored_soil = np.zeros_like(drain_crop)
        colored_soil[dirt_mask > 0] = [0, 165, 255] # 주황색 (BGR)
        # 투명도(Alpha)를 주어 원본과 합성
        cv2.addWeighted(colored_soil, 0.6, drain_crop, 1.0, 0, drain_crop)
        soil_result_img[dr_y1:dr_y2, dr_x1:dr_x2] = drain_crop
        # =================================================================

        # 최종 막힘 비율 계산 로직
        debris_ratio = (valid_debris_area / drain_area) * 100
        soil_ratio = (dirt_area / drain_area) * 100
        
        # 쓰레기와 흙 픽셀이 겹칠 수 있으므로 최대 100%로 제한
        total_obstruction_ratio = min(debris_ratio + soil_ratio, 100.0)

        return {
            "status": "SUCCESS",
            "total_obstruction_ratio": round(total_obstruction_ratio, 2),
            "debris_ratio": round(debris_ratio, 2),
            "soil_ratio": round(soil_ratio, 2),
            "confidence_score": round(drain_conf, 4),
            "message": "분석 완료",
            "yolo_result_img": results[0].plot(),
            "processed_img": processed_img,
            "soil_result_img": soil_result_img # 흙 탐지 결과 이미지 추가
        }

# =====================================================================
# 2. 스트림릿(Streamlit) 웹 대시보드 UI
# =====================================================================
st.set_page_config(page_title="비전 AI 분석 대시보드", layout="wide")
st.title("👁️ 하수구 막힘 비전 AI 분석기 (YOLO + OpenCV 하이브리드)")
st.markdown("업로드된 CCTV 사진을 **YOLOv8 모델(쓰레기)**과 **OpenCV(흙/퇴적물)**로 분석하여 종합 막힘 비율을 추출합니다.")

st.sidebar.header("⚙️ 시스템 설정")
# st.text_input에 value 값으로 기본 경로 지정됨
model_path = st.sidebar.text_input("학습된 YOLO 모델 경로 (.pt)", value="D:\\smartdrain\\ai-vision\\ai-training\\best.pt")

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

    uploaded_files = st.file_uploader("📸 CCTV 하수구 사진들을 올려주세요 (여러 장 가능)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"총 **{len(uploaded_files)}**장의 이미지가 업로드되었습니다.")
        st.markdown("---")
        
        batch_data = [] 

        for idx, file in enumerate(uploaded_files):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_path = tmp_file.name

            with st.spinner(f"[{file.name}] 이미지 전처리 및 YOLO/OpenCV 분석 중..."):
                result = analyzer.analyze_image(tmp_path)

            with st.expander(f"결과 보기: {file.name} - 총 막힘 비율 {result.get('total_obstruction_ratio', 0)}%", expanded=True):
                # 4개의 열로 분할하여 흙 탐지 결과까지 표시
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.caption("1. 원본 이미지")
                    st.image(Image.open(file), use_column_width=True)
                
                if result["status"] == "SUCCESS":
                    with col2:
                        st.caption("2. OpenCV 전처리 (대비 강화)")
                        st.image(cv2.cvtColor(result["processed_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                    with col3:
                        st.caption(f"3. YOLO 탐지 (쓰레기: {result['debris_ratio']}%)")
                        st.image(cv2.cvtColor(result["yolo_result_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                    with col4:
                        st.caption(f"4. OpenCV 흙 탐지 (흙: {result['soil_ratio']}%)")
                        # 흙이 주황색으로 표시된 이미지 출력
                        st.image(cv2.cvtColor(result["soil_result_img"], cv2.COLOR_BGR2RGB), use_column_width=True)
                else:
                    st.error(f"분석 실패: {result['message']}")
            
            os.remove(tmp_path)

            # batch_data에 흙 비율 및 통합 비율 분리하여 저장
            batch_data.append({
                "파일명": file.name,
                "분석 상태": result.get("status", "ERROR"),
                "총 막힘비율(%)": result.get('total_obstruction_ratio', 0.0),
                "쓰레기비율(%)": result.get('debris_ratio', 0.0),
                "흙비율(%)": result.get('soil_ratio', 0.0),
                "YOLO신뢰도(배수구)": result.get('confidence_score', 0.0)
            })

        st.markdown("---")
        st.subheader("📊 YOLO & OpenCV 하이브리드 비전 분석 결과 요약")
        df = pd.DataFrame(batch_data)
        st.dataframe(df, use_container_width=True)

        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 비전 분석 결과 CSV로 다운로드",
            data=csv_data,
            file_name="vision_hybrid_results.csv",
            mime="text/csv"
        )