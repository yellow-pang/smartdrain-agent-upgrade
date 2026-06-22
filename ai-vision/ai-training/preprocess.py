import cv2
import numpy as np
import os

# 💡 핵심 1: 한글 파일명/경로명에서도 이미지를 안전하게 읽어오는 함수
def imread_korean(path):
    try:
        img_array = np.fromfile(path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        return None

# 💡 핵심 2: 한글 파일명/경로명으로 이미지를 안전하게 저장하는 함수
def imwrite_korean(filename, img, params=None):
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)
        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        return False

def preprocess_image(input_path, output_path):
    # 기존 cv2.imread 대신 우회 함수 사용
    img = imread_korean(input_path)
    
    # 💡 핵심 3: 방어 로직 (이미지가 깨졌거나 못 읽었으면 그냥 패스)
    if img is None:
        print(f"⚠️ 이미지를 읽을 수 없습니다. 건너뜁니다: {input_path}")
        return

    # [수정됨] 원근 보정(자르기/확대)을 제거하고 전체 이미지를 안전하게 리사이징
    resized_img = cv2.resize(img, (640, 640))

    # 밝기/대비 보정 (야간/흐린 날씨 대비)
    # alpha: 대비 (1.0~3.0), beta: 밝기 (0~100)
    final_img = cv2.convertScaleAbs(resized_img, alpha=1.2, beta=10)
    
    # 기존 cv2.imwrite 대신 우회 함수 사용
    imwrite_korean(output_path, final_img)
    print(f"✅ 처리 완료: {output_path}")

# ==========================================
# 실행부: raw_data 폴더의 모든 이미지를 처리
# ==========================================
# 알려주신 경로를 여기에 적용했습니다. (r을 붙여 윈도우 경로 인식 오류 방지)
INPUT_DIR = r'ai-vision\ai-training\raw_data'
OUTPUT_DIR = r'ai-vision\ai-training\prepared_data'

if not os.path.exists(OUTPUT_DIR): 
    os.makedirs(OUTPUT_DIR)

# 파일 목록을 가져와서 반복
for f in os.listdir(INPUT_DIR):
    # 이미지 확장자인 경우만 실행 (시스템 숨김 파일 등 방지)
    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
        # os.path.join을 사용해 경로와 파일명을 안전하게 합쳐줍니다.
        input_path = os.path.join(INPUT_DIR, f)
        output_path = os.path.join(OUTPUT_DIR, f)
        preprocess_image(input_path, output_path)