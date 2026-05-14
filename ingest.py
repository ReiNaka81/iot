"""
ingest.py
./logs に置かれた .json を監視し、SSH トンネル越しの MongoDB へ投入する常駐スクリプト。

期待する JSON 形式 (csv_to_json.py の出力):
    [
      {"timestamp": "...", "x": 0.0, "y": 0.0, "z": 0.0},
      ...
    ]
配列の各要素を 1 ドキュメントとして insert_many する。
処理が成功したファイルは削除する。

実行:
    python3 ingest.py
"""
import json
import os
import time

import pymongo
from sshtunnel import SSHTunnelForwarder

LOG_DIR = "./logs"
POLL_INTERVAL_SEC = 2
STABLE_AGE_SEC = 1.0  # FTP 書き込み完了を待つマージン

# SSH 設定 (演習サーバ)
SSH_HOST = "133.19.7.2"
SSH_PORT = 22
SSH_USERNAME = "iot"
SSH_PASSWORD = "!0TeXpER!mENt"

# MongoDB 設定 (SSH 越し)
DB_HOST = "192.168.1.4"
DB_PORT = 59501
DB_NAME = "iot"
COLLECTION_NAME = "accel_raw"


def is_stable(path: str) -> bool:
    """mtime からSTABLE_AGE_SEC以上経過していれば書込完了とみなす。"""
    try:
        return (time.time() - os.path.getmtime(path)) >= STABLE_AGE_SEC
    except FileNotFoundError:
        return False


def process_file(path: str, collection) -> int:
    """1 つの .json を読み、配列の各要素を insert_many する。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"JSON top-level is not a list: {path}")
    if not data:
        return 0
    collection.insert_many(data)
    return len(data)


def main():
    os.makedirs(LOG_DIR, exist_ok=True)

    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USERNAME,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(DB_HOST, DB_PORT),
    ) as tunnel:
        client = pymongo.MongoClient("127.0.0.1", tunnel.local_bind_port)
        collection = client[DB_NAME][COLLECTION_NAME]

        print(f"watching: {os.path.abspath(LOG_DIR)}")
        print(
            f"target:   mongodb {DB_HOST}:{DB_PORT}/{DB_NAME}.{COLLECTION_NAME} "
            f"(via SSH {SSH_HOST})"
        )
        print("Ctrl+C で停止")

        try:
            while True:
                for name in sorted(os.listdir(LOG_DIR)):
                    if not name.endswith(".json"):
                        continue
                    path = os.path.join(LOG_DIR, name)
                    if not is_stable(path):
                        continue
                    try:
                        n = process_file(path, collection)
                        os.remove(path)
                        print(f"inserted {n} docs from {name}, removed")
                    except Exception as e:
                        print(f"ERROR on {name}: {e}")
                time.sleep(POLL_INTERVAL_SEC)
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
