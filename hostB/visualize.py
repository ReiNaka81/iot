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
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # 折れ線グラフ（分散値）
    ax1.plot(times, variances, color='blue', marker='o', label='Variance')
    ax1.set_xlabel('Time Window')
    ax1.set_ylabel('Variance', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # 状態のテキスト表示
    for i, state in enumerate(states):
        ax1.text(times[i], variances[i], f'  {state}', fontsize=9, verticalalignment='bottom')

    plt.title('Walk/RUN/STILL classification')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # グラフを表示（または保存）
    plt.show()

if __name__ == "__main__":
    visualize()
