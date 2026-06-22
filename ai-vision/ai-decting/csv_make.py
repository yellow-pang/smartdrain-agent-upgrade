import json

# XGBoost 학습을 위한 가상 시나리오 데이터 (그룹별 묶음 방식)
# 각 상태(양호, 주의, 위험, 판단불가)를 Key로 하고, 해당 데이터를 리스트로 묶었습니다.
grouped_data = {
    "양호(good)": [
        {
            "obstruction_ratio": 0.10, 
            "confidence_score": 0.95, 
            "water_level": 0.15, 
            "flow_velocity": 0.80
        },
        {
            "obstruction_ratio": 0.05, 
            "confidence_score": 0.98, 
            "water_level": 0.10, 
            "flow_velocity": 0.85
        }
    ],
    
    "주의(caution)": [
        {
            "obstruction_ratio": 0.65, 
            "confidence_score": 0.88, 
            "water_level": 0.45, 
            "flow_velocity": 0.40
        },
        {
            "obstruction_ratio": 0.55, 
            "confidence_score": 0.90, 
            "water_level": 0.35, 
            "flow_velocity": 0.50
        }
    ],
    
    "위험(danger)": [
        {
            "obstruction_ratio": 0.90, 
            "confidence_score": 0.92, 
            "water_level": 0.85, 
            "flow_velocity": 0.15
        },
        {
            "obstruction_ratio": 0.85, 
            "confidence_score": 0.94, 
            "water_level": 0.90, 
            "flow_velocity": 0.10
        }
    ],
    
    "판단불가(unknown)": [
        # 카메라 가려짐 등 (-1.0 처리)
        {
            "obstruction_ratio": -1.0, 
            "confidence_score": 0.00, 
            "water_level": 0.20, 
            "flow_velocity": 0.70
        },
        {
            "obstruction_ratio": -1.0, 
            "confidence_score": 0.00, 
            "water_level": 0.75, 
            "flow_velocity": 0.30
        }
    ]
}

# 파이썬 딕셔너리를 깔끔한 JSON 문자열로 변환
# ensure_ascii=False: 한글 깨짐 방지
# indent=4: 보기 좋게 줄바꿈 및 들여쓰기
json_result = json.dumps(grouped_data, ensure_ascii=False, indent=4)

print("=== 📦 그룹화된 XGBoost 학습용 JSON 데이터 ===")
print(json_result)

# 파일로 저장하기
output_filename = "xgboost_grouped_data.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(grouped_data, f, ensure_ascii=False, indent=4)
    
print(f"\n✅ '{output_filename}' 파일로 깔끔하게 저장되었습니다!")