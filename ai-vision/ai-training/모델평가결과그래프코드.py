import pandas as pd
import matplotlib.pyplot as plt
import os

# 한글 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# ============================
# CSV 읽기
# ============================

csv_path = "ai-vision\\ai-training\\yolo,opencv평가결과.csv"

df = pd.read_csv(csv_path)


# 저장 폴더 생성
save_dir = "evaluation_graph"

if not os.path.exists(save_dir):
    os.makedirs(save_dir)


# ============================
# ① 실제 vs 예측 산점도
# ============================

plt.figure(figsize=(8, 8))

plt.scatter(
    df["실제막힘(%)"],
    df["총막힘(%)"],
    s=120,
    alpha=0.7
)

max_val = max(
    df["실제막힘(%)"].max(),
    df["총막힘(%)"].max()
)

plt.plot(
    [0, max_val],
    [0, max_val],
    linestyle="--"
)

plt.xlabel("실제 막힘률 (%)")
plt.ylabel("예측 막힘률 (%)")

plt.title("실제값 vs 예측값")

plt.grid()

plt.savefig(
    f"{save_dir}/01_실제_vs_예측.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

plt.close()



# ============================
# ② 오차 분포 그래프
# ============================

plt.figure(figsize=(14, 6))

plt.bar(
    range(len(df)),
    df["오차(%)"]
)

mae = df["오차(%)"].mean()

plt.axhline(
    mae,
    linestyle="--",
    label=f"평균 오차 {mae:.1f}%"
)

plt.axhline(
    30,
    linestyle=":"
)

plt.xlabel("샘플")

plt.ylabel("오차 (%)")

plt.title("오차 분포")

plt.legend()

plt.grid()

plt.savefig(
    f"{save_dir}/02_오차분포.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

plt.close()



# ============================
# ③ YOLO 신뢰도 vs 오차
# ============================

plt.figure(figsize=(8, 6))

plt.scatter(
    df["YOLO신뢰도"],
    df["오차(%)"],
    s=140,
    alpha=0.7
)

plt.xlabel("YOLO Confidence")

plt.ylabel("오차 (%)")

plt.title("YOLO 신뢰도 vs 오차")

plt.grid()

plt.savefig(
    f"{save_dir}/03_신뢰도_vs_오차.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

plt.close()


print("\n저장 완료")
print("폴더 위치 → evaluation_graph/")