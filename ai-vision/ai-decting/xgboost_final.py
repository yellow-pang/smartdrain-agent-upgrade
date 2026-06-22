import json
import numpy as np
import xgboost as xgb
import pandas as pd

# ==========================================
# 1. JSON 데이터 불러오기 및 파싱
# ==========================================
def load_and_parse_data(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        grouped_data = json.load(f)

    X = [] # 특징 데이터 (Feature)
    y = [] # 정답 라벨 (Label)

    # 문자열 라벨을 머신러닝이 이해할 수 있는 숫자로 매핑
    label_mapping = {
        "양호(good)": 0,
        "주의(caution)": 1,
        "위험(danger)": 2,
        "판단불가(unknown)": 3
    }

    # JSON 구조를 순회하며 X, y 리스트에 담기
    for label_str, items in grouped_data.items():
        label_idx = label_mapping[label_str]
        
        for item in items:
            features = [
                item["obstruction_ratio"], 
                item["confidence_score"], 
                item["water_level"], 
                item["flow_velocity"]
            ]
            X.append(features)
            y.append(label_idx)

    # XGBoost 학습을 위해 numpy 배열로 변환
    X = np.array(X)
    y = np.array(y)
    
    return X, y, label_mapping

# ==========================================
# 2. XGBoost 모델 학습
# ==========================================
def train_xgboost_model(X, y):
    print("🚀 XGBoost 모델 학습을 시작합니다...")
    
    # 분류(Classification)용 XGBoost 모델 설정
    model = xgb.XGBClassifier(
        objective='multi:softprob', # 다중 분류 설정
        num_class=4,                # 클래스 개수 (양호, 주의, 위험, 판단불가)
        max_depth=4,                # 트리의 최대 깊이
        learning_rate=0.1,          # 학습률
        n_estimators=100,           # 만들 트리의 개수
        random_state=42             # 결과 고정용
    )

    # 데이터 학습 진행
    model.fit(X, y)
    print("✅ 모델 학습 완료!")
    
    # 학습된 모델 저장 (백엔드 서버에서 이 파일을 불러와서 사용합니다)
    model.save_model("sewer_xgboost_model.json")
    print("💾 모델이 'sewer_xgboost_model.json'으로 저장되었습니다.")
    
    return model

# ==========================================
# 3. 새로운 데이터로 예측 테스트
# ==========================================
def predict_new_data(model, label_mapping, new_data_dict):
    # 역매핑 딕셔너리 생성 (0 -> "양호(good)")
    reverse_mapping = {v: k for k, v in label_mapping.items()}
    
    # 딕셔너리를 XGBoost가 읽을 수 있는 2차원 배열 형식으로 변환
    features = np.array([[
        new_data_dict["obstruction_ratio"],
        new_data_dict["confidence_score"],
        new_data_dict["water_level"],
        new_data_dict["flow_velocity"]
    ]])
    
    # DataFrame으로 변환하여 특성(Feature) 이름과 함께 전달하면 경고 메시지를 방지할 수 있습니다.
    feature_names = ["obstruction_ratio", "confidence_score", "water_level", "flow_velocity"]
    df_features = pd.DataFrame(features, columns=feature_names)
    
    # 예측 수행
    pred_idx = model.predict(df_features)[0]
    pred_probs = model.predict_proba(df_features)[0]
    
    result_label = reverse_mapping[pred_idx]
    confidence = pred_probs[pred_idx] * 100
    
    print(f"\n[예측 테스트 결과]")
    print(f"입력 데이터: {new_data_dict}")
    print(f"👉 예측 상태: {result_label} (확률: {confidence:.1f}%)")
    
    return result_label

# ==========================================
# 실행부
# ==========================================
if __name__ == "__main__":
    json_file_path = "xgboost_grouped_data.json"
    
    # 1. 데이터 로드
    try:
        X, y, label_map = load_and_parse_data(json_file_path)
        
        # 2. 모델 학습
        trained_model = train_xgboost_model(X, y)
        
        # 3. 가상의 새로운 센서 데이터 및 YOLO 결과로 예측해보기
        # 상황 A: 쓰레기도 많고, 수위도 매우 높은 상황
        test_case_1 = {
            "obstruction_ratio": 0.88,
            "confidence_score": 0.93,
            "water_level": 0.80,
            "flow_velocity": 0.12
        }
        
        # 상황 B: 카메라는 가려졌지만(-1.0), 수위가 높아서 위험한 상황
        test_case_2 = {
            "obstruction_ratio": -1.0,
            "confidence_score": 0.0,
            "water_level": 0.85,
            "flow_velocity": 0.20
        }
        
        predict_new_data(trained_model, label_map, test_case_1)
        predict_new_data(trained_model, label_map, test_case_2)
        
    except FileNotFoundError:
        print(f"❌ '{json_file_path}' 파일을 찾을 수 없습니다. 먼저 더미 데이터를 생성해주세요.")