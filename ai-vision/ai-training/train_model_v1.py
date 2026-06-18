from ultralytics import YOLO
import os

# 현재 파일(train_model.py) 기준으로 dataset 폴더를 찾음
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'ai-vision\\ai-training\\dataset')
DATA_YAML_PATH = r'D:\smartdrain\ai-vision\ai-training\dataset\data.yaml'# 로보플로우에서 받은 data.yaml 파일

# 1. 모델 로드 (가벼운 Nano 모델 사용)
model = YOLO('yolov8n.pt')

# 2. 데이터 증강이 포함된 학습 설정
# YOLOv8은 train() 내부에서 증강 설정을 아주 잘 처리합니다.
model.train(
    data=DATA_YAML_PATH,
    epochs=100,           # 학습 횟수
    imgsz=640,            # 이미지 크기
    batch=16,             # 배치 사이즈
    name='sewer_model',
    augment=True,
    cache=False,
    # [강력한 실시간 데이터 증강 설정]
    mosaic=1.0,           # 4장의 이미지를 합쳐 객체 인식률 향상
    fliplr=0.5,           # 좌우 반전
    flipud=0.2,           # 상하 반전
    mixup=0.1             # 이미지 혼합을 통한 강인함 강화
)