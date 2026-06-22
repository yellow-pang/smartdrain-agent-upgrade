import xgboost as xgb
import pandas as pd
import json

# ==========================================
# 1. 학습된 XGBoost 모델(JSON) 불러오기
# ==========================================
print("🚀 저장된 XGBoost 뇌(Model)를 불러오는 중...")
model = xgb.XGBClassifier()

try:
    # 앞에서 학습 후 저장했던 바로 그 json 파일을 가져와서 장착합니다!
    model.load_model("sewer_xgboost_model.json")
    print("✅ 모델 로딩 완료!\n")
except xgb.core.XGBoostError:
    print("❌ 'sewer_xgboost_model.json' 파일을 찾을 수 없습니다. 학습 코드를 먼저 실행해주세요.")
    exit()

# 결과 해석용 라벨 딕셔너리 (학습할 때 썼던 순서와 동일해야 합니다)
label_mapping = {
    0: "양호(good)",
    1: "주의(caution)",
    2: "위험(danger)",
    3: "판단불가(unknown)"
}

# ==========================================
# 2. JSON 파일에서 센서 및 YOLO 데이터 불러오기
# ==========================================
json_file_path = "xgboost_grouped_data.json"
print(f"📂 '{json_file_path}' 파일에서 데이터를 불러오는 중...")

try:
    with open(json_file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    # --- [에러 해결 방어 로직] ---
    # JSON 파일이 어떤 형태로 저장되어 있든 억지로 리스트로 맞춰줍니다.
    if isinstance(raw_data, dict):
        if "obstruction_ratio" in raw_data:
            # 1. 단일 객체 { ... } 로만 저장된 경우 리스트로 감싸기
            sensor_data_list = [raw_data]
        else:
            # 2. { "양호": [ ... ] } 형태로 저장된 경우 내용물만 뽑아내기
            sensor_data_list = []
            for group, items in raw_data.items():
                sensor_data_list.extend(items)
    elif isinstance(raw_data, list):
        # 3. 정상적인 [ { ... }, { ... } ] 리스트 형태인 경우
        sensor_data_list = raw_data
    else:
        sensor_data_list = []
        
    print(f"✅ 총 {len(sensor_data_list)}개의 데이터 로딩 완료!\n")
except FileNotFoundError:
    print(f"❌ '{json_file_path}' 파일을 찾을 수 없습니다. 같은 폴더에 파일이 있는지 확인해주세요.")
    exit()

# ==========================================
# 3. 데이터별로 위험도 예측(Predict) 실행
# ==========================================
print("📊 데이터별 침수 위험도 분석 결과\n" + "-"*40)

for data in sensor_data_list:
    # 1) XGBoost에 넣기 위해 딕셔너리를 DataFrame(표) 형태로 변환합니다.
    df_input = pd.DataFrame([[
        data["obstruction_ratio"],
        data["confidence_score"],
        data["water_level"],
        data["flow_velocity"]
    ]], columns=["obstruction_ratio", "confidence_score", "water_level", "flow_velocity"])
    
    # 2) 불러온 모델로 예측 수행! (0.01초도 안 걸립니다)
    pred_idx = model.predict(df_input)[0]          # 예측된 라벨 번호 (0, 1, 2, 3)
    pred_probs = model.predict_proba(df_input)[0]  # 그렇게 생각한 확신도(확률)
    
    # 3) 결과 번호를 다시 한글로 변환
    result_label = label_mapping[pred_idx]
    confidence = pred_probs[pred_idx] * 100
    
    # 4) 화면에 예쁘게 출력
    data_number = data.get("데이터 번호", "알수없음")
    print(f"📌 대상 데이터 : 데이터 번호 {data_number}")
    print(f"   - 입력 데이터 : 막힘비율({data['obstruction_ratio']}), 수위({data['water_level']})")
    
    if "위험" in result_label:
        print(f"   🚨 AI 최종 판단 : {result_label} (확신도: {confidence:.1f}%)\n")
    else:
        print(f"   👉 AI 최종 판단 : {result_label} (확신도: {confidence:.1f}%)\n")

print("-" * 40)