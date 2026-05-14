"""
pipeline.py
/logs ディレクトリを監視し、新しい CSV を見つけ次第:
    1. csv_to_json.csv_to_docs() で JSON 形式の dict リストに変換
    2. チームメンバの insert_single() で 1ドキュメントずつ MongoDB に投入
    3. 処理済み CSV を削除

このスクリプトが「Host A の receiver.py(/logs に CSV を吐く)」と
「チームメンバの insert_single(JSON を MongoDB に入れる)」を繋ぐ。

使い方:
    python3 pipeline.py [--logs ./logs] [--interval 2]
"""
import argparse
import sys
import time
from pathlib import Path

# 同じディレクトリの csv_to_json.py を再利用
sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_to_json import csv_to_docs

# チームメンバが提供する insert_single モジュールに置き換わる前提。
# 受領前はこのファイル内のスタブで動作確認する。
try:
    from insert_single import insert_single
except ImportError:
    def insert_single(doc: dict) -> None:
        """プレースホルダ。実装が届き次第 insert_single.py で上書きされる。"""
        print(f"[stub] insert_single({doc})", flush=True)


# MongoDB 接続情報 (IP 確定後に書き換え。実際に使うのは insert_single 側)
MONGO_HOST = "TBD"
MONGO_PORT = 27017
MONGO_DB = "iot"
MONGO_COLLECTION = "accel_raw"

DEFAULT_LOGS_DIR = "./logs"
DEFAULT_POLL_SEC = 2.0
STABLE_AGE_SEC = 1.0  # mtime がこの秒数経つまでは「書込中かも」としてスキップ


def is_stable(path: Path) -> bool:
    try:
        return (time.time() - path.stat().st_mtime) >= STABLE_AGE_SEC
    except FileNotFoundError:
        return False


def process_csv(path: Path) -> int:
    """1つの CSV を読んで insert_single() で投入し、ファイルを削除する。"""
    docs = csv_to_docs(str(path))
    for doc in docs:
        insert_single(doc)
    path.unlink()
    return len(docs)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", default=DEFAULT_LOGS_DIR,
                   help="監視対象ディレクトリ (default: ./logs)")
    p.add_argument("--interval", type=float, default=DEFAULT_POLL_SEC,
                   help="ポーリング間隔(秒) (default: 2)")
    return p.parse_args()


def main():
    args = parse_args()
    logs_dir = Path(args.logs)
    logs_dir.mkdir(parents=True, exist_ok=True)

    print(f"# watching:       {logs_dir.resolve()}", flush=True)
    print(f"# poll interval:  {args.interval}s", flush=True)
    print(f"# mongo target:   {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}.{MONGO_COLLECTION}",
          flush=True)

    try:
        while True:
            for csv_path in sorted(logs_dir.glob("*.csv")):
                if not is_stable(csv_path):
                    continue
                try:
                    n = process_csv(csv_path)
                    print(f"# inserted {n} docs from {csv_path.name}, deleted",
                          flush=True)
                except Exception as e:
                    print(f"# ERROR on {csv_path.name}: {e}", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n# stopped", flush=True)


if __name__ == "__main__":
    main()
