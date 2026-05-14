"""
receiver.py
Spresense (sender.ino, KX126) から CSV "x,y,z" を受信し、
タイムスタンプを付けて 10秒ごとに CSV にまとめて /logs に保存する。

CSV 形式: timestamp,x,y,z
分類処理 (STILL/WALK/RUN) は MapReduce 側で行うため、ここでは生データのみ扱う。

使い方:
    python3 receiver.py [--port COM7] [--baud 115200]
"""
import argparse
import os
import sys
import time
from datetime import datetime

import serial

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD = 115200
FLUSH_INTERVAL_SEC = 10  # CSV 書き出し間隔
LOG_DIR = "logs"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    return p.parse_args()


def flush(buffer: list) -> None:
    """buffer 内のレコードを /logs/accel_*.csv に保存。"""
    if not buffer:
        return
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"accel_{ts}.csv"
    local_path = os.path.join(LOG_DIR, filename)

    with open(local_path, "w") as f:
        f.write("timestamp,x,y,z\n")
        for r in buffer:
            f.write(f"{r['t']},{r['x']:.3f},{r['y']:.3f},{r['z']:.3f}\n")
    print(f"# saved: {local_path} ({len(buffer)} rows)", flush=True)


def main():
    args = parse_args()
    ser = serial.Serial(args.port, args.baud, timeout=2)
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"# connected: {args.port} @ {args.baud}", flush=True)

    buffer: list = []
    last_flush = time.time()

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
                        continue
                    now = datetime.now().isoformat(timespec="milliseconds")
                    buffer.append({"t": now, "x": x, "y": y, "z": z})
                    print(f"{now} x={x:+.3f} y={y:+.3f} z={z:+.3f}", flush=True)

            if time.time() - last_flush >= FLUSH_INTERVAL_SEC:
                flush(buffer)
                buffer = []
                last_flush = time.time()

    except KeyboardInterrupt:
        print("\n# stopping...", flush=True)
    finally:
        flush(buffer)
        ser.close()
        print("# closed", flush=True)


if __name__ == "__main__":
    main()
    sys.exit(0)
