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


"""
import os
from ultralytics import YOLO

# 2. 경로 설정 (구글 드라이브)
GOOGLE_DRIVE_DIR = '/content/drive/MyDrive/하수도학습'
DATA_YAML_PATH = os.path.join(GOOGLE_DRIVE_DIR, 'dataset_v2', 'data_v2.yaml')

# 💡 핵심: 이름을 명확히 바꾼 로컬 30에포크 가중치를 불러옵니다.
LOCAL_WEIGHTS_PATH = os.path.join(GOOGLE_DRIVE_DIR, '/content/drive/MyDrive/하수도학습/runs/detect/sewer_model_v3-2/weights/local_30ep.pt')

# 3. 모델 로드
model = YOLO(LOCAL_WEIGHTS_PATH)

if __name__ == '__main__':
    print(f"🚀 [A 계정] local_30ep.pt를 이어받아 중간 60 에포크(누적 90) 학습을 시작합니다!")

    model.train(
        data=DATA_YAML_PATH,
        epochs=60,                # 남은 120 에포크 중 절반인 60 진행
        imgsz=800,
        batch=8,

        # 🌟 결과물을 구글 드라이브 runs 폴더에 안전하게 실시간 저장
        project=os.path.join(GOOGLE_DRIVE_DIR, 'runs'),
        name='sewer_model_v3_part1', # 폴더명: part1

        patience=30,
        cache=False,

        # V3 핵심 증강 옵션
        augment=True,
        mosaic=1.0,
        mixup=0.15,
        fliplr=0.5,
        flipud=0.2,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,

        # ⚠️ 아직 150 에포크의 끝이 아니므로 모자이크를 끄지 않습니다!
        close_mosaic=0,

        dropout=0.1
    )
    print("✅ A 계정 60 에포크 학습 완료! 구글 드라이브에서 결과물을 확인하세요.")
"""
"""
    🚀 [A 계정] local_30ep.pt를 이어받아 중간 60 에포크(누적 90) 학습을 시작합니다!
Ultralytics 8.4.72 🚀 Python-3.12.13 torch-2.11.0+cu128 CUDA:0 (Tesla T4, 14913MiB)
engine/trainer: agnostic_nms=False, amp=True, angle=1.0, augment=True, auto_augment=randaugment, batch=8, bgr=0.0, box=7.5, cache=False, cfg=None, classes=None, close_mosaic=0, cls=0.5, cls_pw=0.0, compile=False, conf=None, copy_paste=0.0, copy_paste_mode=flip, cos_lr=False, cutmix=0.0, data=/content/drive/MyDrive/하수도학습/dataset_v2/data_v2.yaml, degrees=0.0, deterministic=True, device=None, dfl=1.5, dnn=False, dropout=0.1, dynamic=False, embed=None, end2end=None, epochs=60, erasing=0.4, exist_ok=False, fliplr=0.5, flipud=0.2, format=torchscript, fraction=1.0, freeze=None, half=False, hsv_h=0.015, hsv_s=0.5, hsv_v=0.4, imgsz=800, int8=False, iou=0.7, keras=False, kobj=1.0, line_width=None, lr0=0.01, lrf=0.01, mask_ratio=4, max_det=300, mixup=0.15, mode=train, model=/content/drive/MyDrive/하수도학습/runs/detect/sewer_model_v3-2/weights/local_30ep.pt, momentum=0.937, mosaic=1.0, multi_scale=0.0, name=sewer_model_v3_part1, nbs=64, nms=False, opset=None, optimize=False, optimizer=auto, overlap_mask=True, patience=30, perspective=0.0, plots=True, pose=12.0, pretrained=True, profile=False, project=/content/drive/MyDrive/하수도학습/runs, rect=False, resume=False, retina_masks=False, rle=1.0, save=True, save_conf=False, save_crop=False, save_dir=/content/drive/MyDrive/하수도학습/runs/sewer_model_v3_part1, save_frames=False, save_json=False, save_period=-1, save_txt=False, scale=0.5, seed=0, shear=0.0, show=False, show_boxes=True, show_conf=True, show_labels=True, simplify=True, single_cls=False, source=None, split=val, stream_buffer=False, task=detect, time=None, tracker=botsort.yaml, translate=0.1, val=True, verbose=True, vid_stride=1, visualize=False, warmup_bias_lr=0.1, warmup_epochs=3.0, warmup_momentum=0.8, weight_decay=0.0005, workers=8, workspace=None
Downloading https://ultralytics.com/assets/Arial.ttf to '/root/.config/Ultralytics/Arial.ttf': 100% ━━━━━━━━━━━━ 755.1KB 108.2MB/s 0.0s

                   from  n    params  module                                       arguments                     
  0                  -1  1      1392  ultralytics.nn.modules.conv.Conv             [3, 48, 3, 2]                 
  1                  -1  1     41664  ultralytics.nn.modules.conv.Conv             [48, 96, 3, 2]                
  2                  -1  2    111360  ultralytics.nn.modules.block.C2f             [96, 96, 2, True]             
  3                  -1  1    166272  ultralytics.nn.modules.conv.Conv             [96, 192, 3, 2]               
  4                  -1  4    813312  ultralytics.nn.modules.block.C2f             [192, 192, 4, True]           
  5                  -1  1    664320  ultralytics.nn.modules.conv.Conv             [192, 384, 3, 2]              
  6                  -1  4   3248640  ultralytics.nn.modules.block.C2f             [384, 384, 4, True]           
  7                  -1  1   1991808  ultralytics.nn.modules.conv.Conv             [384, 576, 3, 2]              
  8                  -1  2   3985920  ultralytics.nn.modules.block.C2f             [576, 576, 2, True]           
  9                  -1  1    831168  ultralytics.nn.modules.block.SPPF            [576, 576, 5]                 
 10                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']          
 11             [-1, 6]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 12                  -1  2   1993728  ultralytics.nn.modules.block.C2f             [960, 384, 2]                 
 13                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']          
 14             [-1, 4]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 15                  -1  2    517632  ultralytics.nn.modules.block.C2f             [576, 192, 2]                 
 16                  -1  1    332160  ultralytics.nn.modules.conv.Conv             [192, 192, 3, 2]              
 17            [-1, 12]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 18                  -1  2   1846272  ultralytics.nn.modules.block.C2f             [576, 384, 2]                 
 19                  -1  1   1327872  ultralytics.nn.modules.conv.Conv             [384, 384, 3, 2]              
 20             [-1, 9]  1         0  ultralytics.nn.modules.conv.Concat           [1]                           
 21                  -1  2   4207104  ultralytics.nn.modules.block.C2f             [960, 576, 2]                 
 22        [15, 18, 21]  1   3776854  ultralytics.nn.modules.head.Detect           [2, 16, None, [192, 384, 576]]
Model summary: 170 layers, 25,857,478 parameters, 25,857,462 gradients, 79.1 GFLOPs

Transferred 475/475 items from pretrained weights
Freezing layer 'model.22.dfl.conv.weight'
AMP: running Automatic Mixed Precision (AMP) checks...
Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 100% ━━━━━━━━━━━━ 5.3MB 265.2MB/s 0.0s
AMP: checks passed ✅
train: Fast image access ✅ (ping: 0.6±0.2 ms, read: 3.3±1.5 MB/s, size: 3122.7 KB)
train: Scanning /content/drive/MyDrive/하수도학습/dataset_v2/train/labels.cache... 63 images, 5 backgrounds, 0 corrupt: 100% ━━━━━━━━━━━━ 63/63 13.9Mit/s 0.0s
train: /content/drive/MyDrive/하수도학습/dataset_v2/train/images/ChatGPT Image 2026년 6월 12일 오후 07_36_53 (2)_png.rf.ezfG9ktmIOy6Gam9YqzE.png: 1 duplicate labels removed
train: /content/drive/MyDrive/하수도학습/dataset_v2/train/images/ChatGPT Image 2026년 6월 15일 오전 09_46_19 (1)_png.rf.1tTyaZgWC2O4olwBBxOW.png: 1 duplicate labels removed
train: /content/drive/MyDrive/하수도학습/dataset_v2/train/images/ChatGPT Image 2026년 6월 15일 오전 09_50_03 (1)_png.rf.ioPWpJE6Hg4hyP2yUCKV.png: 1 duplicate labels removed
train: /content/drive/MyDrive/하수도학습/dataset_v2/train/images/ChatGPT Image 2026년 6월 15일 오전 09_50_04 (7)_png.rf.NF0Wc3O8JYiNkbqFYX8S.png: 3 duplicate labels removed
train: /content/drive/MyDrive/하수도학습/dataset_v2/train/images/ChatGPT Image 2026년 6월 15일 오전 09_50_04 (8)_png.rf.EfGpfpM6dj2umEg2ZuZn.png: 1 duplicate labels removed
albumentations: Blur(p=0.01, blur_limit=(3, 7)), MedianBlur(p=0.01, blur_limit=(3, 7)), ToGray(p=0.01, method='weighted_average', num_output_channels=3), CLAHE(p=0.01, clip_limit=(1.0, 4.0), tile_grid_size=(8, 8))
val: Fast image access ✅ (ping: 0.5±0.2 ms, read: 3.7±0.7 MB/s, size: 3149.2 KB)
val: Scanning /content/drive/MyDrive/하수도학습/dataset_v2/valid/labels.cache... 18 images, 0 backgrounds, 0 corrupt: 100% ━━━━━━━━━━━━ 18/18 1.1Mit/s 0.0s
val: /content/drive/MyDrive/하수도학습/dataset_v2/valid/images/ChatGPT Image 2026년 6월 12일 오후 05_37_45 (9)_png.rf.IYd6QZ9cpBgQT5aPBylo.png: 1 duplicate labels removed
val: /content/drive/MyDrive/하수도학습/dataset_v2/valid/images/ChatGPT Image 2026년 6월 15일 오전 09_46_19 (7)_png.rf.h3pqYPEIEhVAm5eEulqC.png: 1 duplicate labels removed
optimizer: 'optimizer=auto' found, ignoring 'lr0=0.01' and 'momentum=0.937' and determining best 'optimizer', 'lr0' and 'momentum' automatically... 
optimizer: AdamW(lr=0.001667, momentum=0.9) with parameter groups 77 weight(decay=0.0), 84 weight(decay=0.0005), 83 bias(decay=0.0)
Plotting labels to /content/drive/MyDrive/하수도학습/runs/sewer_model_v3_part1/labels.jpg... 
Image sizes 800 train, 800 val
Using 2 dataloader workers
Logging results to /content/drive/MyDrive/하수도학습/runs/sewer_model_v3_part1
Starting training for 60 epochs...

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       1/60      5.23G     0.9422     0.9493       1.01        472        800: 100% ━━━━━━━━━━━━ 8/8 7.2s/it 57.3s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.7s/it 5.3s
                   all         18       1002      0.765      0.795      0.811      0.688

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       2/60      6.35G     0.9583     0.9431      1.019        360        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.6s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.8it/s 1.1s
                   all         18       1002      0.742      0.807      0.775      0.644

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       3/60      6.35G     0.9684     0.9605      1.002        645        800: 100% ━━━━━━━━━━━━ 8/8 1.8it/s 4.5s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.6it/s 0.8s
                   all         18       1002       0.79      0.767      0.767      0.604

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       4/60      6.36G     0.8808     0.9585     0.9917        431        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.4it/s 0.8s
                   all         18       1002      0.757      0.723      0.786      0.606

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       5/60      6.36G     0.9544     0.9822      1.004        630        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 5.0s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.8it/s 1.1s
                   all         18       1002      0.748      0.742      0.767      0.574

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       6/60      6.97G     0.9814      1.017      1.029        548        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.1it/s 0.9s
                   all         18       1002      0.783      0.728      0.789      0.599

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       7/60      6.97G      0.933     0.9494      1.008        437        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 4.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.4it/s 0.8s
                   all         18       1002      0.666      0.787      0.679      0.557

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       8/60      6.97G      0.947      0.917     0.9936        463        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 5.1s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.2it/s 0.9s
                   all         18       1002      0.632      0.695      0.625      0.474

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
       9/60      6.97G      1.011      1.014       1.05        798        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 4.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.7it/s 1.2s
                   all         18       1002      0.437      0.693      0.506      0.303

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      10/60      6.97G       1.02     0.9829      1.015        597        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.7s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.5it/s 0.8s
                   all         18       1002      0.294      0.421      0.283      0.161

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      11/60      6.97G     0.9543      1.003      1.012        572        800: 100% ━━━━━━━━━━━━ 8/8 1.8it/s 4.6s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.3it/s 0.9s
                   all         18       1002      0.398      0.389      0.271      0.176

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      12/60      6.97G      0.902     0.9474     0.9908        532        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.4it/s 0.8s
                   all         18       1002      0.443      0.595      0.395       0.25

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      13/60      6.97G     0.9423      0.986      0.987        548        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 4.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.9it/s 1.1s
                   all         18       1002      0.657      0.735      0.684      0.504

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      14/60      6.97G      0.999     0.9838      1.026        389        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.3it/s 0.9s
                   all         18       1002      0.684      0.648      0.713      0.559

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      15/60      6.97G     0.9281      0.924      1.006        705        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.6s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.2it/s 0.9s
                   all         18       1002      0.632      0.682      0.721      0.558

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      16/60      6.97G     0.9631     0.9448      1.018        426        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.5it/s 0.8s
                   all         18       1002      0.672      0.668      0.721      0.553

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      17/60      6.97G     0.9959      1.061      1.028        652        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 4.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.8it/s 1.1s
                   all         18       1002      0.695      0.689      0.705      0.536

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      18/60      6.97G      1.003     0.9915      1.005        535        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.7s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.7it/s 1.2s
                   all         18       1002      0.405      0.747      0.535      0.413

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      19/60      6.97G     0.8895     0.8872     0.9823        392        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.1it/s 0.9s
                   all         18       1002      0.622      0.602      0.631      0.514

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      20/60      6.97G     0.9548     0.9442      1.014        636        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 5.0s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.6it/s 0.8s
                   all         18       1002      0.694      0.643      0.691      0.578

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      21/60      6.97G     0.9191     0.9087     0.9955        348        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.9it/s 1.1s
                   all         18       1002      0.797       0.69       0.77      0.628

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      22/60      6.97G     0.9502     0.9245      1.013        558        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.7s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.4it/s 0.8s
                   all         18       1002      0.755      0.678      0.758      0.611

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      23/60      6.97G     0.8978     0.8892     0.9898        393        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.5it/s 0.8s
                   all         18       1002       0.75      0.756      0.763      0.642

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      24/60      6.97G     0.9599     0.9241      1.004        571        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 4.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.4it/s 0.8s
                   all         18       1002      0.781      0.734      0.785      0.637

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      25/60      6.97G     0.8587     0.8756     0.9766        540        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.6s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.8it/s 1.1s
                   all         18       1002      0.714      0.787       0.82      0.639

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      26/60      6.97G     0.8994     0.8757     0.9862        438        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.6s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 3.3it/s 0.6s
                   all         18       1002      0.775       0.81      0.811       0.66

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      27/60      6.97G     0.8929     0.9317     0.9971        184        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.7s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.3it/s 0.9s
                   all         18       1002      0.784      0.738      0.778      0.658

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      28/60      6.97G     0.8843     0.8721      0.959        392        800: 100% ━━━━━━━━━━━━ 8/8 1.3it/s 5.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.4it/s 0.8s
                   all         18       1002       0.79      0.734      0.759      0.643

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      29/60      6.97G     0.9028     0.8794     0.9906        771        800: 100% ━━━━━━━━━━━━ 8/8 1.6it/s 4.9s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.6it/s 0.8s
                   all         18       1002      0.786      0.772      0.774      0.658

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      30/60      6.97G     0.8133     0.7999     0.9565        656        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.6s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.3it/s 0.9s
                   all         18       1002        0.8      0.757      0.786      0.672

      Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
      31/60      6.97G     0.8627       0.82     0.9604        671        800: 100% ━━━━━━━━━━━━ 8/8 1.7it/s 4.8s
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 2.5it/s 0.8s
                   all         18       1002      0.825      0.743      0.811      0.685
EarlyStopping: Training stopped early as no improvement observed in last 30 epochs. Best results observed at epoch 1, best model saved as best.pt.
To update EarlyStopping(patience=30) pass a new patience value, i.e. `patience=300` or use `patience=0` to disable EarlyStopping.

31 epochs completed in 0.113 hours.
Optimizer stripped from /content/drive/MyDrive/하수도학습/runs/sewer_model_v3_part1/weights/last.pt, 52.1MB
Optimizer stripped from /content/drive/MyDrive/하수도학습/runs/sewer_model_v3_part1/weights/best.pt, 52.1MB

Validating /content/drive/MyDrive/하수도학습/runs/sewer_model_v3_part1/weights/best.pt...
Ultralytics 8.4.72 🚀 Python-3.12.13 torch-2.11.0+cu128 CUDA:0 (Tesla T4, 14913MiB)
Model summary (fused): 93 layers, 25,840,918 parameters, 0 gradients, 78.7 GFLOPs
                 Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 2/2 1.8s/it 3.6s
                   all         18       1002      0.814      0.769      0.816      0.703
                debris         16        984      0.664      0.649      0.651      0.488
                 drain         18         18      0.965      0.889      0.982      0.918
Speed: 0.3ms preprocess, 184.2ms inference, 0.0ms loss, 5.7ms postprocess per image
Results saved to /content/drive/MyDrive/하수도학습/runs/sewer_model_v3_part1
✅ A 계정 60 에포크 학습 완료! 구글 드라이브에서 결과물을 확인하세요.
    """