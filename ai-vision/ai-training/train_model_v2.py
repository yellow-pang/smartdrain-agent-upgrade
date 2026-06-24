from ultralytics import YOLO
import os

# 1. 새로운 V2 데이터셋 경로 설정
# 현재 실행 중인 파일의 위치를 기준으로 dataset_v2 폴더 안의 data_v2.yaml을 찾습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_YAML_PATH = os.path.join(BASE_DIR, 'dataset_v2', 'data_v2.yaml')

# (참고) 만약 파일 실행 시 경로 에러가 난다면, 아래 절대 경로 주석을 풀고 사용하세요.
# DATA_YAML_PATH = r'D:\smartdrain\ai-vision\ai-training\dataset_v2\data_v2.yaml'

# 2. 모델 로드 (성능 업그레이드)
# 이전의 가장 가벼운 yolov8n.pt 대신, 쓰레기를 더 정교하게 잡아낼 수 있는 yolov8s.pt(Small)를 사용합니다.
model = YOLO('yolov8s.pt')

# 3. 비 안 오는 날 환경에 맞춘 V2 학습 설정
if __name__ == '__main__':
    print(f"🚀 V2 학습을 시작합니다. 데이터셋 경로: {DATA_YAML_PATH}")
    
    model.train(
        data=DATA_YAML_PATH,
        epochs=150,             # 쓰레기의 다양한 형태를 충분히 배우도록 150번 학습
        imgsz=640,              # 이미지 크기
        batch=16,               # 컴퓨터 사양에 맞춰 조절 가능 (Out of Memory 에러 발생 시 8로 줄이세요)
        name='sewer_model_v2',  # 기존 폴더를 덮어쓰지 않고 runs/detect/sewer_model_v2 에 새로 저장
        patience=30,            # 30번 반복하는 동안 성능 향상이 없으면 똑똑하게 조기 종료
        cache=False,
        
        # [비 안 오는 맑은 날씨 맞춤 데이터 증강]
        augment=True,
        mosaic=1.0,           # 4장을 합쳐서 화면을 복잡하게 만듦 (작은 담배꽁초, 낙엽 탐지력 극대화)
        mixup=0.1,            # 투명하게 이미지를 겹쳐 모델의 객체 분별력을 높임
        fliplr=0.5,           # 좌우 반전 (좌우가 바뀐 쓰레기 형태 학습)
        flipud=0.2,           # 상하 반전 (가끔 카메라가 뒤집혀 있을 때나 쓰레기가 뒤집힌 상황 대비)
        
        # 햇빛에 의한 강한 그림자와 맑은 날 특유의 대비를 학습하도록 색상 변환 유지
        hsv_h=0.015,          # 색상 약간 변경 (다양한 색상의 쓰레기 대응)
        hsv_s=0.5,            # 채도 변경
        hsv_v=0.4             # 밝기 변경 (그늘진 하수구 안과 햇빛 비치는 하수구 밖 동시 대비)
    )
    print("✅ V2 학습이 완료되었습니다! runs/detect/sewer_model_v2/weights/best.pt 를 확인하세요.")