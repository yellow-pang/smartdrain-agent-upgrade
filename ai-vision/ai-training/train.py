from ultralytics import YOLO
import os

# 1. 로보플로우에서 다운로드받아 압축을 푼 폴더 경로를 지정합니다.
# 이미지가 있는 폴더 경로 (예: 'dataset' 폴더로 이름을 바꾸고 프로젝트와 같은 위치에 두시면 편리합니다)
DATASET_DIR = os.path.abspath('dataset') 

# 2. '야말(YAML)' 설정을 코드가 자동으로 생성합니다. (사용자가 직접 파일 만들 필요 없음!)
# 이미지가 PNG 형식이어도 YOLO가 내부적으로 자동 매칭하므로 걱정하지 않으셔도 됩니다.
auto_yaml_content = f"""
path: {DATASET_DIR}      # 데이터셋 루트 절대경로
train: train/images      # 학습용 PNG 이미지 경로 (상대경로)
val: valid/images        # 검증용 PNG 이미지 경로 (상대경로)

nc: 2
names: ['drain', 'debris']
"""

yaml_path = os.path.join(DATASET_DIR, 'data_auto.yaml')

# 폴더 존재 여부 확인 후 자동화 진행
if not os.path.exists(DATASET_DIR):
    print(f"❌ 에러: '{DATASET_DIR}' 폴더를 찾을 수 없습니다.")
    print("💡 해결 방법: 다운로드받은 폴더명을 'dataset'으로 변경하여 소스코드 파일과 같은 폴더에 놓아주세요.")
else:
    # data_auto.yaml 파일 자동 생성 (사용자 개입 배제)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(auto_yaml_content.strip())
    print(f"✅ YAML 설정이 이미지 폴더 기반으로 자동 생성되었습니다: {yaml_path}")

    # 3. YOLO 모델 로드 (가장 가볍고 효율적인 YOLOv8 Nano 사용)
    model = YOLO('yolov8n.pt')

    # 4. 데이터 증강(Augmentation) 옵션과 함께 학습 시작
    print("🚀 PNG 이미지 데이터셋으로 학습을 시작합니다. 잠시만 기다려주세요...")
    model.train(
        data=yaml_path,       # 코드가 자동 생성한 YAML 경로 전달
        epochs=100,           # 학습 반복 횟수
        imgsz=640,            # 이미지 크기 (640x640)
        batch=16,             # 배치 크기
        name='sewer_blockage_detection',
        
        # [강력한 데이터 증강 설정]
        mosaic=1.0,           # 4장의 이미지를 무작위로 합성 (하수구의 작은 이물질 인식률 극대화)
        degrees=15.0,         # 최대 15도 무작위 회전 (다양한 각도 대처)
        fliplr=0.5,           # 좌우 반전
        flipud=0.2,           # 상하 반전 (거꾸로 찍힌 구도 대처)
        brightness=0.2,       # 밝기 변화 (날씨 및 시간대 변화 대응)
        contrast=0.2,         # 대비 변화 (철망과 쓰레기 간의 경계 구분력 향상)
        mixup=0.1             # 두 이미지를 겹쳐 강인한 모델 생성
    )
    print("✅ 학습이 완료되었습니다!")
    print("최적의 가중치 파일은 'runs/detect/sewer_blockage_detection/weights/best.pt'에 저장되었습니다.")