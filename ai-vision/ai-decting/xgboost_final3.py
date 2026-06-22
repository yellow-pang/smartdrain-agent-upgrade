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
# 2. JSON 파일에서 센서 및 AI 비전 데이터 불러오기
# ==========================================
# V3에서 생성한 JSON 파일 이름을 사용합니다.
json_file_path = "vision_v3_results.json"
print(f"📂 '{json_file_path}' 파일에서 데이터를 불러오는 중...")

try:
    with open(json_file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    # JSON 파일이 리스트 형태로 저장되어 있다고 가정합니다.
    if isinstance(raw_data, list):
        sensor_data_list = raw_data
    else:
        print("❌ JSON 데이터 형식이 올바르지 않습니다. 리스트 형태여야 합니다.")
        sensor_data_list = []
        
    print(f"✅ 총 {len(sensor_data_list)}개의 데이터 로딩 완료!\n")
except FileNotFoundError:
    print(f"❌ '{json_file_path}' 파일을 찾을 수 없습니다. '{json_file_path}' 파일이 있는지 확인해주세요.")
    exit()

# ==========================================
# 3. 데이터별로 위험도 예측(Predict) 실행
# ==========================================
print("📊 데이터별 침수 위험도 분석 결과\n" + "-"*40)

for data in sensor_data_list:
    # V3 데이터 구조에 맞게 DataFrame을 구성합니다.
    # 참고: XGBoost 모델이 학습할 때 사용한 feature 순서와 동일해야 합니다.
    # 현재 xgboost_final.py 코드를 보면 학습 시 아래 4개 feature를 사용했습니다.
    # 1. obstruction_ratio (총 막힘 비율)
    # 2. confidence_score (신뢰도)
    # 3. water_level (수위 - JSON에 없으므로 가상 데이터 사용)
    # 4. flow_velocity (유속 - JSON에 없으므로 가상 데이터 사용)
    
    # JSON에 없는 가상 센서 데이터 (임의의 값 적용)
    # 실제 환경에서는 센서에서 값을 읽어와야 합니다.
    mock_water_level = 0.5 
    mock_flow_velocity = 0.3
    
    df_input = pd.DataFrame([[
        data.get("total_obstruction_ratio", 0.0),
        data.get("confidence_score", 0.0),
        mock_water_level,
        mock_flow_velocity
    ]], columns=["obstruction_ratio", "confidence_score", "water_level", "flow_velocity"])
    
    # 2) 불러온 모델로 예측 수행
    pred_idx = model.predict(df_input)[0]          # 예측된 라벨 번호
    pred_probs = model.predict_proba(df_input)[0]  # 예측 확신도
    
    # 3) 결과 번호를 다시 한글로 변환
    result_label = label_mapping.get(pred_idx, "알수없음")
    confidence = pred_probs[pred_idx] * 100
    
    # 4) 화면에 예쁘게 출력
    file_name = data.get("file_name", "알수없음")
    print(f"📌 대상 파일 : {file_name}")
    print(f"   - 비전 AI 분석 : 총 막힘({data.get('total_obstruction_ratio', 0.0)}%), 쓰레기({data.get('debris_ratio', 0.0)}%), 흙({data.get('soil_ratio', 0.0)}%)")
    print(f"   - 가상 센서 데이터 : 수위({mock_water_level}), 유속({mock_flow_velocity})")
    
    if "위험" in result_label:
        print(f"   🚨 AI 최종 판단 : {result_label} (확신도: {confidence:.1f}%)\n")
    else:
        print(f"   👉 AI 최종 판단 : {result_label} (확신도: {confidence:.1f}%)\n")

print("-" * 40)