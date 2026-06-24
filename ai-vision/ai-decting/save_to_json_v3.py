import json
import os
import glob
from ai_pipeline_v3 import SewerAIAnalyzerV3

def process_images_to_json(image_folder, output_json_path):
    print(f"🚀 AI 모델 로딩 중... (V3 하이브리드 모델)")
    # V3 모델 로드 (YOLOv8 + OpenCV 흙 탐지)
    analyzer = SewerAIAnalyzerV3(model_path='best.pt')
    
    # 분석 결과를 담을 빈 리스트
    json_results = []
    
    # 폴더 내의 모든 이미지 파일 찾기 (jpg, png, jpeg 등)
    image_paths = glob.glob(os.path.join(image_folder, "*.[jp][pn]*g"))
    
    if not image_paths:
        print(f"⚠️ '{image_folder}' 폴더에 이미지가 없습니다.")
        return

    print(f"총 {len(image_paths)}장의 이미지 분석을 시작합니다...\n" + "-"*50)

    for img_path in image_paths:
        file_name = os.path.basename(img_path)
        
        # V3 파이프라인 분석 실행 (HSV나 그림자 임계값은 기본값 사용)
        result = analyzer.analyze_image(img_path)
        
        # V3에서 새롭게 추가된 상세 비율 데이터들 추출
        data = {
            "file_name": file_name,
            "status": result["status"],
            "message": result["message"],
            "total_obstruction_ratio": result.get("total_obstruction_ratio", 0.0),
            "debris_ratio": result.get("debris_ratio", 0.0),
            "soil_ratio": result.get("soil_ratio", 0.0),
            "confidence_score": result.get("confidence_score", 0.0)
        }
        
        json_results.append(data)
        print(f"✔️ 분석 완료: {file_name}")
        print(f"   ↳ 총 막힘: {data['total_obstruction_ratio']}% (쓰레기: {data['debris_ratio']}%, 흙: {data['soil_ratio']}%) | 신뢰도: {data['confidence_score']}")

    # JSON 파일로 저장하기
    with open(output_json_path, 'w', encoding='utf-8') as f:
        # 한글 깨짐 방지(ensure_ascii=False) 및 보기 좋게 들여쓰기(indent=4)
        json.dump(json_results, f, ensure_ascii=False, indent=4)
        
    print("-" * 50)
    print(f"✅ 모든 분석이 끝났습니다! 결과가 '{output_json_path}'에 저장되었습니다.")

if __name__ == "__main__":
    # 1. 테스트할 사진들이 들어있는 폴더 이름 (미리 만들어두세요)
    TARGET_FOLDER = "test_images" 
    
    # 2. 저장될 JSON 파일 이름 (V3 버전임을 명시)
    OUTPUT_FILE = "vision_v3_results.json"
    
    # 실행
    process_images_to_json(TARGET_FOLDER, OUTPUT_FILE)