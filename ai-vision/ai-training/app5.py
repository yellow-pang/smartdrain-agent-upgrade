import streamlit as st
import cv2
import numpy as np

# ==========================================
# 1. 페이지 설정 및 제목
# ==========================================
st.set_page_config(page_title="HSV 튜닝 시뮬레이터", layout="wide")
st.title("🎛️ 흙(퇴적물) 색상 범위(HSV) 튜닝 시뮬레이터")
st.markdown("애매한 하수구 사진을 업로드하고 좌측 슬라이더를 움직여 최적의 **`lower_brown`**과 **`upper_brown`** 값을 찾아보세요.")

# ==========================================
# 2. 사이드바 (슬라이더 UI)
# ==========================================
st.sidebar.header("⚙️ HSV 색상 범위 조절")
st.sidebar.caption("OpenCV 기준 (H: 0~179, S: 0~255, V: 0~255)")

st.sidebar.subheader("🎨 범위 1 (기존: 황토/일반 흙)")
h1_min = st.sidebar.slider("H (색상) 하한 1", 0, 179, 10)
s1_min = st.sidebar.slider("S (채도) 하한 1", 0, 255, 40)
v1_min = st.sidebar.slider("V (명도) 하한 1", 0, 255, 20)
h1_max = st.sidebar.slider("H (색상) 상한 1", 0, 179, 35)
s1_max = st.sidebar.slider("S (채도) 상한 1", 0, 255, 255)
v1_max = st.sidebar.slider("V (명도) 상한 1", 0, 255, 200)

st.sidebar.markdown("---")
st.sidebar.subheader("🎨 범위 2 (기존: 어두운/붉은 흙)")
h2_min = st.sidebar.slider("H (색상) 하한 2", 0, 179, 0)
s2_min = st.sidebar.slider("S (채도) 하한 2", 0, 255, 20)
v2_min = st.sidebar.slider("V (명도) 하한 2", 0, 255, 10)
h2_max = st.sidebar.slider("H (색상) 상한 2", 0, 179, 10)
s2_max = st.sidebar.slider("S (채도) 상한 2", 0, 255, 200)
v2_max = st.sidebar.slider("V (명도) 상한 2", 0, 255, 150)

# ==========================================
# 3. 메인 화면 (이미지 업로드 및 분석)
# ==========================================
uploaded_file = st.file_uploader("📸 테스트할 하수구 이미지를 업로드하세요", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # 1. 파일 읽기 및 이미지 디코딩
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    # 2. BGR을 HSV 색공간으로 변환
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 3. 슬라이더 값을 배열로 변환
    lower_brown1 = np.array([h1_min, s1_min, v1_min])
    upper_brown1 = np.array([h1_max, s1_max, v1_max])
    mask1 = cv2.inRange(hsv_img, lower_brown1, upper_brown1)
    
    lower_brown2 = np.array([h2_min, s2_min, v2_min])
    upper_brown2 = np.array([h2_max, s2_max, v2_max])
    mask2 = cv2.inRange(hsv_img, lower_brown2, upper_brown2)
    
    # 4. 두 마스크 합치기 (OR 연산)
    combined_mask = cv2.bitwise_or(mask1, mask2)
    
    # 5. 모폴로지 연산 (노이즈 제거 및 덩어리 키우기) - 이전 단계에서 논의된 기법 적용
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    combined_mask = cv2.dilate(combined_mask, kernel, iterations=2)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    # 6. 결과 오버레이 (주황색 덧칠하기)
    result_img = img.copy()
    colored_soil = np.zeros_like(img)
    colored_soil[combined_mask > 0] = [0, 165, 255]  # OpenCV는 BGR 기준
    cv2.addWeighted(colored_soil, 0.6, result_img, 1.0, 0, result_img)
    
    # 7. Streamlit 출력을 위해 색상 공간 변환 (BGR -> RGB)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
    
    # 8. 화면 분할 출력
    st.markdown("### 📊 분석 결과")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image(img_rgb, caption="1. 원본 이미지", use_column_width=True)
    with col2:
        # 마스크는 흑백 이미지이므로 clamp=True 필요
        st.image(combined_mask, caption="2. 흙 탐지 마스크 (흰색=흙)", use_column_width=True, clamp=True)
    with col3:
        st.image(result_rgb, caption="3. 최종 오버레이", use_column_width=True)
        
    # 9. 찾아낸 최적의 값을 바로 복사할 수 있게 출력
    st.markdown("---")
    st.success("✅ 슬라이더 조절 후 마음에 드는 결과가 나왔다면, 아래 값을 복사해서 본 코드에 적용하세요!")
    st.code(f"""
# 찾은 최적의 HSV 값
lower_brown1 = np.array([{h1_min}, {s1_min}, {v1_min}])
upper_brown1 = np.array([{h1_max}, {s1_max}, {v1_max}])

lower_brown2 = np.array([{h2_min}, {s2_min}, {v2_min}])
upper_brown2 = np.array([{h2_max}, {s2_max}, {v2_max}])
    """, language="python")