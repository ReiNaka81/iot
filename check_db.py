"""
check_db.py
MongoDB の accel_raw コレクションの中身を確認・出力する。

使い方:
    python3 check_db.py [--limit 10]        # 最新N件をターミナルに表示
    python3 check_db.py --out output.json   # 全件をJSONファイルに出力
"""
import argparse
import json

import pymongo
from sshtunnel import SSHTunnelForwarder

SSH_HOST = "133.19.7.2"
SSH_PORT = 22
SSH_USERNAME = "iot"
SSH_PASSWORD = "!0TeXpER!mENt"

DB_HOST = "192.168.1.4"
DB_PORT = 59501
DB_NAME = "iot"
COLLECTION_NAME = "accel_raw"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=10, help="ターミナル表示件数 (default: 10)")
    p.add_argument("--out", help="出力先JSONファイルパス (指定すると全件をファイルに保存)")
    return p.parse_args()


def main():
    args = parse_args()

    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USERNAME,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(DB_HOST, DB_PORT),
    ) as tunnel:
        client = pymongo.MongoClient("127.0.0.1", tunnel.local_bind_port)
        col = client[DB_NAME][COLLECTION_NAME]

        total = col.count_documents({})
        print(f"総ドキュメント数: {total}")

        if args.out:
            docs = [
                {k: v for k, v in doc.items() if k != "_id"}
                for doc in col.find().sort("timestamp", 1)
            ]
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(docs, f, ensure_ascii=False, indent=2)
            print(f"{len(docs)} 件を {args.out} に保存しました。")
        else:
            print(f"最新 {args.limit} 件:")
            print("-" * 50)
            for doc in col.find().sort("_id", -1).limit(args.limit):
                doc.pop("_id", None)
                print(doc)


if __name__ == "__main__":
    main()
