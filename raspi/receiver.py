"""
receiver.py
Spresense (sender.ino, KX126) から CSV "x,y,z" を受信し、
ノルムの移動分散から STILL / WALK / RUN を分類して標準出力する。
さらに 10 秒ごとに分類結果を CSV にまとめて FTP 送信する。

使い方:
    python3 receiver.py [--port COM7] [--baud 115200]
"""
import argparse
import math
import os
import sys
import time
from collections import deque
from datetime import datetime

import serial

from ftp import upload

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD = 115200
WINDOW = 20              # 約1秒 @ 20Hz
FLUSH_INTERVAL_SEC = 10  # FTP 送信間隔

# 分類しきい値 (G^2): 環境に合わせて要調整
STILL_VAR_MAX = 0.02   # これ未満は STILL
WALK_VAR_MAX  = 0.50   # これ未満は WALK、それ以上は RUN

LOG_DIR = "logs"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    return p.parse_args()


def classify(var: float) -> str:
    if var < STILL_VAR_MAX:
        return "STILL"
    if var < WALK_VAR_MAX:
        return "WALK"
    return "RUN"


def flush(buffer: list) -> None:
    """buffer 内のレコードを CSV に保存して FTP 送信。失敗時はローカルだけ残す。"""
    if not buffer:
        return
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"accel_{ts}.csv"
    local_path = os.path.join(LOG_DIR, filename)

    with open(local_path, "w") as f:
        f.write("timestamp,x,y,z\n")
        for r in buffer:
            f.write(
                f"{r['t']},{r['x']:.3f},{r['y']:.3f},{r['z']:.3f}\n"
            )
    print(f"# saved: {local_path} ({len(buffer)} rows)", flush=True)

    

def main():
    args = parse_args()
    ser = serial.Serial(args.port, args.baud, timeout=2)
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"# connected: {args.port} @ {args.baud}", flush=True)

    norms = deque(maxlen=WINDOW)
    buffer: list = []
    last_flush = time.time()
    prev_state = None

    try:
        while True:
            raw = ser.readline()
            if raw:
                line = raw.decode(errors="ignore").strip()
                parts = line.split(",")
                if len(parts) == 3:
                    try:
                        x, y, z = (float(p) for p in parts)
                    except ValueError:
                        x = None
                    if x is not None:
                        norm = math.sqrt(x * x + y * y + z * z)
                        norms.append(norm)

                        if len(norms) < WINDOW:
                            print(
                                f"x={x:+.3f} y={y:+.3f} z={z:+.3f} "
                                f"|a|={norm:.3f} (warming up)",
                                flush=True,
                            )
                        else:
                            mean = sum(norms) / WINDOW
                            var = sum((n - mean) ** 2 for n in norms) / WINDOW
                            state = classify(var)

                            marker = " *" if state != prev_state else ""
                            prev_state = state
                            now = datetime.now().isoformat(timespec="milliseconds")
                            print(
                                f"{now} x={x:+.3f} y={y:+.3f} z={z:+.3f} "
                                f"|a|={norm:.3f} var={var:.4f} [{state}]{marker}",
                                flush=True,
                            )
                            buffer.append(
                                {"t": now, "x": x, "y": y, "z": z}
                                )
                                

            # 10 秒経過したら FTP 送信
            if time.time() - last_flush >= FLUSH_INTERVAL_SEC:
                flush(buffer)
                buffer = []
                last_flush = time.time()

    except KeyboardInterrupt:
        print("\n# stopping...", flush=True)
    finally:
        flush(buffer)  # 残りも送信
        ser.close()
        print("# closed", flush=True)


if __name__ == "__main__":
    main()
    sys.exit(0)


import datetime
import sys
import os

def convert_to_csv(input_file, output_file, start_time_str):
    # 開始時刻のパース (例: "2026-05-14T14:23:00.000")
    start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S.%f")
    interval = datetime.timedelta(milliseconds=50) # 50ms = 20Hz
    
    valid_count = 0
    skipped_count = 0

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:
        
        # ヘッダーの書き込み
        fout.write("timestamp,x,y,z\n")
        
        for line in fin:
            line = line.strip()
            parts = line.split(',')
            
            # カンマ区切りで3つの要素がある行のみ処理
            if len(parts) == 3:
                try:
                    # 数値に変換できるかテスト
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])
                    
                    # タイムスタンプの計算
                    current_time = start_time + (interval * valid_count)
                    # .%fはマイクロ秒なので、[:-3]でミリ秒にトリミング
                    time_str = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
                    
                    # 小数点以下3桁に揃えて出力
                    fout.write(f"{time_str},{x:.3f},{y:.3f},{z:.3f}\n")
                    valid_count += 1
                except ValueError:
                    # 数値変換エラー（"KX126_WHO_AMI" などのゴミデータ）は無視
                    skipped_count += 1
            else:
                # 3要素でない行も無視
                skipped_count += 1

    print(f"変換完了: {output_file}")
    print(f" - 有効データ出力数: {valid_count} 行")
    print(f" - スキップした行数: {skipped_count} 行")

if __name__ == "__main__":
    # 使い方: python convert_log.py 入力ファイル名 出力ファイル名 開始時刻
    # 引数が足りない場合はデフォルト値で実行テスト
    if len(sys.argv) < 3:
        print("【実行例】 python convert_log.py raw_data.txt output.csv 2026-05-14T14:23:00.000")
        print("※引数なしのため、デフォルト設定で実行します。\n")
        
        # テスト用のファイル名
        input_name = "raw_test.txt"
        output_name = "formatted_test.csv"
        
        # テスト用入力ファイルが存在しない場合は作成する（動作確認用）
        if not os.path.exists(input_name):
            with open(input_name, "w") as f:
                f.write("KX126_WHO_AMI Register Value = 0x38\n0.01,0.09,1.03\n0.01,0.10,1.03\n")
                
        convert_to_csv(input_name, output_name, "2026-05-14T14:23:00.000")
    else:
        in_file = sys.argv[1]
        out_file = sys.argv[2]
        # 第3引数があれば開始時刻とし、無ければデフォルト時刻
        start_t = sys.argv[3] if len(sys.argv) >= 4 else "2026-05-14T14:23:00.000"
        
        convert_to_csv(in_file, out_file, start_t)













