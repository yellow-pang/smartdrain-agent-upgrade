import json
import numpy as np
import xgboost as xgb
import pandas as pd
import os

# ==========================================
# 1. 여러 JSON 파일 불러오기 및 병합
# ==========================================
def load_and_merge_multiple_files():
    # 파일 경로와 정답 라벨(0, 1, 2, 3) 매핑
    file_mapping = {
        "xgboost_input_data/good.json": 0,       # 양호
        "xgboost_input_data/caution.json": 1,    # 주의
        "xgboost_input_data/danger.json": 2,     # 위험
        "xgboost_input_data/unknown.json": 3     # 판단불가
    }

    X = [] # 특징 데이터 (Feature)
    y = [] # 정답 라벨 (Label)
    
    print("📂 'xgboost_input_data' 폴더에서 4개의 JSON 데이터를 불러옵니다...\n")
    
    total_loaded = 0
    
    for file_path, label_idx in file_mapping.items():
        if not os.path.exists(file_path):
            print(f"  ❌ 에러: '{file_path}' 파일을 찾을 수 없습니다.")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data_list = json.load(f)
            
            # (방어 로직) 만약 리스트가 아니라 단일 딕셔너리면 리스트로 감싸줌
            if isinstance(data_list, dict):
                data_list = [data_list]
                
            for item in data_list:
                features = [
                    item.get("obstruction_ratio", 0.0), 
                    item.get("confidence_score", 0.0), 
                    item.get("water_level", 0.0), 
                    item.get("flow_velocity", 0.0)
                ]
                X.append(features)
                y.append(label_idx)
                
            print(f"  ✔️ '{file_path}' 에서 {len(data_list)}개 데이터 로딩 완료! (라벨: {label_idx})")
            total_loaded += len(data_list)

    print(f"\n✅ 총 {total_loaded}개의 데이터 병합 완료!")
    
    return np.array(X), np.array(y)

# ==========================================
# 2. XGBoost 모델 학습
# ==========================================
def train_xgboost_model(X, y):
    if len(X) == 0:
        print("❌ 학습할 데이터가 없습니다. 폴더와 파일 경로를 확인해주세요.")
        exit()

    print("\n🚀 XGBoost 모델 학습을 시작합니다...")
    
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
    
    # 학습된 모델 저장
    model.save_model("sewer_xgboost_model.json")
    print("💾 모델이 'sewer_xgboost_model.json'으로 저장되었습니다.")
    
    return model

# ==========================================
# 3. 새로운 데이터로 예측 테스트
# ==========================================
def predict_new_data(model, new_data_dict):
    # 결과 해석용 역매핑 딕셔너리
    reverse_mapping = {
        0: "양호(good)",
        1: "주의(caution)",
        2: "위험(danger)",
        3: "판단불가(unknown)"
    }
    
    # 딕셔너리를 XGBoost가 읽을 수 있는 2차원 배열 형식으로 변환
    features = np.array([[
        new_data_dict["obstruction_ratio"],
        new_data_dict["confidence_score"],
        new_data_dict["water_level"],
        new_data_dict["flow_velocity"]
    ]])
    
    # DataFrame으로 변환하여 특성(Feature) 이름과 함께 전달
    feature_names = ["obstruction_ratio", "confidence_score", "water_level", "flow_velocity"]
    df_features = pd.DataFrame(features, columns=feature_names)
    
    # 예측 수행
    pred_idx = model.predict(df_features)[0]
    pred_probs = model.predict_proba(df_features)[0]
    
    result_label = reverse_mapping[pred_idx]
    confidence = pred_probs[pred_idx] * 100
    
    print(f"\n[예측 테스트 결과]")
    print(f"입력 데이터: {new_data_dict}")
    if "위험" in result_label:
        print(f"🚨 예측 상태: {result_label} (확률: {confidence:.1f}%)")
    else:
        print(f"👉 예측 상태: {result_label} (확률: {confidence:.1f}%)")
    
    return result_label

# ==========================================
# 실행부
# ==========================================
if __name__ == "__main__":
    # 1. 4개의 파일에서 데이터 싹 쓸어오기
    X_train, y_train = load_and_merge_multiple_files()
    
    # 2. 모아온 데이터로 모델 학습시키고 JSON 뇌로 저장하기
    trained_model = train_xgboost_model(X_train, y_train)
    
    # 3. 가상의 새로운 센서 데이터 및 YOLO 결과로 예측해보기
    print("\n" + "="*40)
    print("🎯 학습된 AI의 예측 능력을 테스트합니다!")
    
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
    
    predict_new_data(trained_model, test_case_1)
    predict_new_data(trained_model, test_case_2)
    print("="*40)