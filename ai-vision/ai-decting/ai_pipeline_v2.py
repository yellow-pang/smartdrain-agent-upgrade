import cv2
import numpy as np
from ultralytics import YOLO

class SewerAIAnalyzerV2:
    def __init__(self, model_path='best.pt'):
        """
        V2 학습 모델을 로드합니다. (경로 주의: sewer_model_v2)
        """
        self.model = YOLO(model_path)
        # 클래스 인덱스 (data_v2.yaml 기준: 0=debris, 1=drain)
        self.DEBRIS_CLS = 0
        self.DRAIN_CLS = 1

    def preprocess_image(self, image_path):
        """
        [OpenCV 전처리] 맑은 날씨의 강한 그림자를 대비하기 위해 CLAHE 기법 적용
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

    def analyze_image(self, image_path):
        """
        이미지를 분석하여 XGBoost로 보낼 최종 데이터를 뽑아냅니다.
        """
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
                if conf > drain_conf: # 하수구가 여러개면 가장 확실한 것 선택
                    drain_conf = conf
                    drain_box = coords
            elif cls == self.DEBRIS_CLS:
                debris_boxes.append((coords, conf))

        # 4. 하수구가 없는 경우
        if drain_box is None:
            return {
                "status": "UNKNOWN",
                "obstruction_ratio": 0.0,
                "confidence_score": 0.0,
                "message": "하수구 미탐지",
                "yolo_result_img": results[0].plot() # 시각화용 이미지
            }

        # 5. 하수구 내부 쓰레기 필터링 및 막힘 비율 계산
        dr_x1, dr_y1, dr_x2, dr_y2 = drain_box
        drain_area = (dr_x2 - dr_x1) * (dr_y2 - dr_y1)
        valid_debris_area = 0.0

        for d_coords, d_conf in debris_boxes:
            d_x1, d_y1, d_x2, d_y2 = d_coords
            center_x = (d_x1 + d_x2) / 2
            center_y = (d_y1 + d_y2) / 2

            # 쓰레기 중심점이 하수구 박스 안에 있을 때만 면적 계산
            if (dr_x1 <= center_x <= dr_x2) and (dr_y1 <= center_y <= dr_y2):
                d_area = (d_x2 - d_x1) * (d_y2 - d_y1)
                valid_debris_area += d_area

        # 비율 계산 (최대 100%)
        obstruction_ratio = min(valid_debris_area / drain_area, 1.0)

        # 6. 최종 결과 반환
        return {
            "status": "SUCCESS",
            "obstruction_ratio": round(obstruction_ratio, 2),
            "confidence_score": round(drain_conf, 4),
            "message": "분석 완료",
            "yolo_result_img": results[0].plot(), # 바운딩 박스가 그려진 이미지
            "processed_img": processed_img        # OpenCV가 보정한 이미지
        }