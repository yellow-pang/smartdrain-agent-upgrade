from ultralytics import YOLO
import os

# 1. 데이터셋 경로 설정 (V2와 동일한 데이터셋 사용)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_YAML_PATH = os.path.join(BASE_DIR, 'dataset_v2', 'data_v2.yaml')

# 2. 모델 로드 (체급 업그레이드: Small -> Medium)
# 파라미터 수가 늘어나서 복잡하게 막힌 쓰레기의 패턴을 훨씬 깊게 이해합니다.
model = YOLO('yolov8m.pt') 

if __name__ == '__main__':
    print(f"🚀 [V3 모델] 강력한 학습을 시작합니다!")
    
    model.train(
        data=DATA_YAML_PATH,
        epochs=150,
        # 💡 개선 1: 이미지 해상도 증가 (VRAM이 부족하다면 다시 640으로 낮추세요)
        # 해상도를 높이면 뭉쳐있는 쓰레기의 디테일을 더 잘 봅니다.
        imgsz=800,              
        batch=8,                # 해상도와 모델 크기를 올렸으므로 배치는 8로 줄입니다.
        name='sewer_model_v3',  # V3 폴더에 새롭게 저장
        patience=30,
        cache=False,
        
        # [데이터 증강 및 V3 핵심 최적화 옵션]
        augment=True,
        mosaic=1.0,           
        mixup=0.15,           # 믹스업 비율을 살짝 올려 겹친 쓰레기에 강해지게 함
        fliplr=0.5,           
        flipud=0.2,           
        hsv_h=0.015,          
        hsv_s=0.5,            
        hsv_v=0.4,
        
        # 💡 개선 2: close_mosaic (최신 YOLO 꿀팁)
        # 총 150번의 학습 중 마지막 10번은 모자이크 증강을 끕니다.
        # 이렇게 하면 모델이 마지막에 "아! 현실의 하수구는 원래 이렇게 생겼지!" 하고 현실 감각을 되찾아 정확도가 폭발적으로 상승합니다.
        close_mosaic=10,
        
        # 💡 개선 3: 과적합 방지 (Dropout)
        # 모델 크기를 키웠으므로, 너무 학습 데이터만 달달 외우지 않도록 방어합니다.
        dropout=0.1
    )
    
    print("✅ V3 학습 완료! runs/detect/sewer_model_v3/weights/best.pt 가 생성되었습니다.")