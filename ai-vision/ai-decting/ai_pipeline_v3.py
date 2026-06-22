import cv2
import numpy as np
from ultralytics import YOLO

class SewerAIAnalyzerV3:
    def __init__(self, model_path='best.pt'):
        """
        V3 학습 모델 및 하이브리드 비전 AI 분석기를 로드합니다.
        (YOLOv8 + OpenCV 흙 탐지 + 명도 기반 내부 구멍 필터링 적용 버전)
        """
        self.model = YOLO(model_path)
        # 클래스 인덱스 (data_v2.yaml 기준: 0=debris, 1=drain)
        self.DEBRIS_CLS = 0
        self.DRAIN_CLS = 1

    def preprocess_image(self, image_path):
        """
        [OpenCV 전처리] 이미지 로드 및 CLAHE 기법 적용
        어두운 하수구 안쪽의 쓰레기를 더 잘 보이게 만들어 줍니다.
        """
        # 이미지 읽기 (한글 경로 깨짐 방지를 위해 numpy로 읽기)
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return None, None
            
        # 원본 이미지 백업
        original_img = img.copy()

        # LAB 색상 공간으로 변환하여 밝기(L) 채널만 평활화 (색상 왜곡 방지)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        
        # 다시 BGR로 변환 (YOLO 입력용)
        enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        return original_img, enhanced_img

    def analyze_image(self, image_path, hsv_params=None, shadow_thresh=45):
        """
        이미지를 분석하여 XGBoost로 보낼 최종 데이터를 뽑아냅니다.
        (YOLO 쓰레기 탐지 + OpenCV 겉면 흙 탐지 융합 방식)
        
        :param hsv_params: 흙 탐지를 위한 HSV 상/하한값 딕셔너리
        :param shadow_thresh: 내부 구멍(어두운 곳)을 제외할 명도(V) 기준값
        """
        
        # 외부에서 hsv_params를 넘기지 않았을 때 사용할 기본값 셋업
        if hsv_params is None:
            hsv_params = {
                'lower1': np.array([10, 40, 20]),
                'upper1': np.array([35, 255, 200]),
                'lower2': np.array([0, 20, 10]),
                'upper2': np.array([10, 200, 150])
            }

        # 1. OpenCV 전처리 실행
        original_img, processed_img = self.preprocess_image(image_path)
        
        if processed_img is None:
            return {"status": "ERROR", "message": "이미지를 읽을 수 없습니다."}

        # 2. YOLO 추론 (conf=0.25 로 약간의 쓰레기도 의심하게 세팅)
        results = self.model.predict(processed_img, conf=0.25, verbose=False)
        boxes = results[0].boxes

        drain_box = None
        drain_conf = 0.0
        debris_boxes = []

        # 3. 객체 분류
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            coords = box.xyxy[0].tolist() # [x1, y1, x2, y2]

            if cls == self.DRAIN_CLS:
                if conf > drain_conf:
                    drain_conf = conf
                    drain_box = coords
            elif cls == self.DEBRIS_CLS:
                debris_boxes.append((coords, conf))

        # 4. 하수구가 없는 경우 예외 처리
        if drain_box is None:
            return {
                "status": "UNKNOWN", 
                "total_obstruction_ratio": 0.0, 
                "debris_ratio": 0.0, 
                "soil_ratio": 0.0,
                "confidence_score": 0.0, 
                "message": "하수구 영역 미탐지", 
                "yolo_result_img": results[0].plot(), 
                "soil_result_img": original_img
            }

        # 5. 하수구 박스 면적 및 내부 쓰레기 비율 계산 (YOLO)
        dr_x1, dr_y1, dr_x2, dr_y2 = map(int, drain_box)
        drain_area = (dr_x2 - dr_x1) * (dr_y2 - dr_y1)
        
        valid_debris_area = 0.0
        for d_coords, d_conf in debris_boxes:
            d_x1, d_y1, d_x2, d_y2 = map(int, d_coords)
            center_x, center_y = (d_x1 + d_x2) / 2, (d_y1 + d_y2) / 2
            
            # 쓰레기 중심점이 하수구 박스 안에 있을 때만 합산
            if (dr_x1 <= center_x <= dr_x2) and (dr_y1 <= center_y <= dr_y2):
                valid_debris_area += (d_x2 - d_x1) * (d_y2 - d_y1)

        # =================================================================
        # 6. 💡 [OpenCV 흙 탐지 알고리즘] 하수구 밑 내부 구멍 필터링 적용
        # =================================================================
        drain_crop = original_img[dr_y1:dr_y2, dr_x1:dr_x2]
        hsv_crop = cv2.cvtColor(drain_crop, cv2.COLOR_BGR2HSV)
        
        # 6-1. 흙 색상 두 가지 범위 마스킹 후 병합
        mask1 = cv2.inRange(hsv_crop, hsv_params['lower1'], hsv_params['upper1'])
        mask2 = cv2.inRange(hsv_crop, hsv_params['lower2'], hsv_params['upper2'])
        dirt_mask = cv2.bitwise_or(mask1, mask2)
        
        # 6-2. 하수구 안쪽 어두운 구멍(그림자) 마스크 생성
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([179, 255, shadow_thresh])
        dark_hole_mask = cv2.inRange(hsv_crop, lower_dark, upper_dark)
        
        # 6-3. 흙 마스크에서 어두운 구멍 영역 강제 제거
        dirt_mask = cv2.bitwise_and(dirt_mask, cv2.bitwise_not(dark_hole_mask))
        
        # 6-4. 모폴로지 연산으로 잔여 노이즈 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dirt_mask = cv2.dilate(dirt_mask, kernel, iterations=2)
        dirt_mask = cv2.morphologyEx(dirt_mask, cv2.MORPH_OPEN, kernel)
        
        dirt_area = cv2.countNonZero(dirt_mask)
        
        # 시각화 이미지 생성 (흙 부분 주황색 하이라이팅)
        soil_result_img = original_img.copy()
        colored_soil = np.zeros_like(drain_crop)
        colored_soil[dirt_mask > 0] = [0, 165, 255]
        
        cv2.addWeighted(colored_soil, 0.6, drain_crop, 1.0, 0, drain_crop)
        soil_result_img[dr_y1:dr_y2, dr_x1:dr_x2] = drain_crop

        # =================================================================
        # 7. 💡 [데이터 융합] 확률적 결합을 통한 최종 막힘 비율 산출
        # =================================================================
        debris_ratio = (valid_debris_area / drain_area) * 100
        soil_ratio = (dirt_area / drain_area) * 100

        # 확률적 결합 방식 (A + B - A*B/100)
        total_obstruction_ratio = (debris_ratio + soil_ratio) - ((debris_ratio * soil_ratio) / 100.0)

        # 8. XGBoost 머신러닝 모델의 Feature로 사용될 최종 산출물 반환
        return {
            "status": "SUCCESS",
            "total_obstruction_ratio": round(total_obstruction_ratio, 2),
            "debris_ratio": round(debris_ratio, 2),
            "soil_ratio": round(soil_ratio, 2),
            "confidence_score": round(drain_conf, 4),
            "message": "분석 완료",
            "yolo_result_img": results[0].plot(), # YOLO 탐지 시각화
            "processed_img": processed_img,       # 전처리된 이미지
            "soil_result_img": soil_result_img    # OpenCV 흙 탐지 시각화
        }