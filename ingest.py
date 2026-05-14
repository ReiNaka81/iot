import os
import json
import pymongo
from sshtunnel import SSHTunnelForwarder

LOG_DIR = "./logs"

# SSH設定
SSH_HOST = '133.19.7.2'
SSH_PORT = 22
SSH_USERNAME = 'iot'
SSH_PASSWORD = '!0TeXpER!mENt'

DB_HOST = '192.168.1.4'
DB_PORT = 59501

# SSHトンネル
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USERNAME,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT)
)

server.start()

client = pymongo.MongoClient('127.0.0.1', server.local_bind_port)
db = client["iot"]
collection = db["accel_raw"]


def ingest():
    files = os.listdir(LOG_DIR)

    for file in files:
        if file.endswith(".json"):
            path = os.path.join(LOG_DIR, file)

            print(f"処理中: {file}")

            # JSON読み込み
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            collection.insert_one({
                "filename": file,
                "data": data
            })

            print("1件INSERT")

            # 処理後削除
            os.remove(path)


if __name__ == "__main__":
    try:
        ingest()
    finally:
        server.stop()