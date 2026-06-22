import json
import os
import glob
from ai_pipeline_v2 import SewerAIAnalyzerV2

def process_images_to_json(image_folder, output_json_path):
    print(f"🚀 AI 모델 로딩 중... (V2 모델)")
    # V2 모델 경로 설정
    analyzer = SewerAIAnalyzerV2(model_path='best.pt')
    
    # 분석 결과를 담을 빈 리스트
    json_results = []
    
    # 폴더 내의 모든 이미지 파일 찾기 (jpg, png 등)
    image_paths = glob.glob(os.path.join(image_folder, "*.[jp][pn]*g"))
    
    if not image_paths:
        print(f"⚠️ '{image_folder}' 폴더에 이미지가 없습니다.")
        return

    print(f"총 {len(image_paths)}장의 이미지 분석을 시작합니다...")

    for img_path in image_paths:
        file_name = os.path.basename(img_path)
        
        # 파이프라인(OpenCV + YOLO) 분석 실행
        result = analyzer.analyze_image(img_path)
        
        # JSON에 저장할 핵심 데이터만 추출 (이미지 파일 자체는 JSON에 못 들어가므로 제외)
        data = {
            "file_name": file_name,
            "status": result["status"],
            "message": result["message"],
            "obstruction_ratio": result.get("obstruction_ratio", 0.0),
            "confidence_score": result.get("confidence_score", 0.0)
        }
        
        json_results.append(data)
        print(f" ✔️ 분석 완료: {file_name} -> 막힘 비율: {data['obstruction_ratio']}, 신뢰도: {data['confidence_score']}")

    # JSON 파일로 저장하기
    with open(output_json_path, 'w', encoding='utf-8') as f:
        # 한글 깨짐 방지(ensure_ascii=False) 및 보기 좋게 들여쓰기(indent=4)
        json.dump(json_results, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ 모든 분석이 끝났습니다! 결과가 '{output_json_path}'에 저장되었습니다.")

if __name__ == "__main__":
    # 1. 테스트할 사진들이 들어있는 폴더 이름 (미리 만들어두세요)
    TARGET_FOLDER = "test_images" 
    
    # 2. 저장될 JSON 파일 이름
    OUTPUT_FILE = "yolo_results.json"
    
    # 실행
    process_images_to_json(TARGET_FOLDER, OUTPUT_FILE)