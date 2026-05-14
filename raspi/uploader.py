"""
uploader.py  (送信側)
receiver.py が ./logs に書き出した CSV を見つけ次第、
csv_to_json で JSON に変換し、SSH トンネル越しの MongoDB へ直接 insert する。
処理が成功した CSV はローカルから削除する。

使い方:
    python3 uploader.py [--logs ./logs] [--interval 2]
"""
import argparse
import sys
import time
from pathlib import Path

import pymongo
from sshtunnel import SSHTunnelForwarder

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sever"))
from csv_to_json import csv_to_docs  # noqa: E402


# SSH 設定
SSH_HOST = "133.19.7.2"
SSH_PORT = 22
SSH_USERNAME = "iot"
SSH_PASSWORD = "!0TeXpER!mENt"

# MongoDB 設定
DB_HOST = "192.168.1.4"
DB_PORT = 59501
DB_NAME = "iot"
COLLECTION_NAME = "accel_raw"

DEFAULT_LOGS_DIR = "./logs"
DEFAULT_POLL_SEC = 2.0
STABLE_AGE_SEC = 1.0


def is_stable(path: Path) -> bool:
    try:
        return (time.time() - path.stat().st_mtime) >= STABLE_AGE_SEC
    except FileNotFoundError:
        return False


def process_csv(csv_path: Path, collection) -> int:
    docs = csv_to_docs(str(csv_path))
    if not docs:
        csv_path.unlink()
        return 0
    collection.insert_many(docs)
    csv_path.unlink()
    return len(docs)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", default=DEFAULT_LOGS_DIR, help="監視ディレクトリ")
    p.add_argument("--interval", type=float, default=DEFAULT_POLL_SEC,
                   help="ポーリング間隔(秒)")
    return p.parse_args()


def main():
    args = parse_args()
    logs_dir = Path(args.logs)
    logs_dir.mkdir(parents=True, exist_ok=True)

    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USERNAME,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(DB_HOST, DB_PORT),
    ) as tunnel:
        client = pymongo.MongoClient("127.0.0.1", tunnel.local_bind_port)
        collection = client[DB_NAME][COLLECTION_NAME]

        print(f"# watching:  {logs_dir.resolve()}")
        print(f"# target:    mongodb {DB_HOST}:{DB_PORT}/{DB_NAME}.{COLLECTION_NAME} (via SSH {SSH_HOST})")
        print(f"# interval:  {args.interval}s")
        print("Ctrl+C で停止")

        try:
            while True:
                for csv_path in sorted(logs_dir.glob("*.csv")):
                    if not is_stable(csv_path):
                        continue
                    try:
                        n = process_csv(csv_path, collection)
                        print(f"# inserted {n} docs from {csv_path.name}, removed")
                    except Exception as e:
                        print(f"# ERROR on {csv_path.name}: {e}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n# stopped")


if __name__ == "__main__":
    main()
