# visualizer.py
import sys
import matplotlib.pyplot as plt

def visualize():
    times = []
    variances = []
    states = []

    # Reducerの出力を1行ずつ読み込む
    for line in sys.stdin:
        if "|" not in line or "Time Window" in line or "---" in line:
            continue
        
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3:
            times.append(parts[0].split('T')[-1]) # 時刻のみ抽出
            variances.append(float(parts[1]))
            states.append(parts[2])

    if not times:
        print("No data to plot.")
        return

    # グラフの作成
    fig, ax1 = plt.subplots(figsize=(14, 6))

    x_idx = range(len(times))

    # 折れ線グラフ（分散値）
    ax1.plot(x_idx, variances, color='blue', marker='o', markersize=4, label='Variance')
    ax1.set_xlabel('Time Window')
    ax1.set_ylabel('Variance', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # 状態のテキスト表示（分散が高い点のみラベル表示）
    threshold = sorted(variances)[-max(1, len(variances) // 10)]
    for i, (state, var) in enumerate(zip(states, variances)):
        if var >= threshold:
            ax1.text(i, var, f'  {state}', fontsize=8, verticalalignment='bottom')

    # X軸は間引いて表示
    step = max(1, len(times) // 20)
    ax1.set_xticks(list(x_idx)[::step])
    ax1.set_xticklabels(times[::step], rotation=45, ha='right', fontsize=8)

    plt.title('Walk/RUN/STILL classification')
    plt.tight_layout()
    
    # グラフを表示（または保存）
    plt.show()

if __name__ == "__main__":
    visualize()
