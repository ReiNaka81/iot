from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder

SSH_HOST = "133.19.7.2"
SSH_PORT = 22
SSH_USERNAME = "iot"
SSH_PASSWORD = "!0TeXpER!mENt"

DB_HOST = "192.168.1.4"
DB_PORT = 59501
DB_NAME = "iot"
COLLECTION_NAME = "accel_raw"


def export():
    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USERNAME,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(DB_HOST, DB_PORT),
    ) as tunnel:
        client = MongoClient("127.0.0.1", tunnel.local_bind_port)
        collection = client[DB_NAME][COLLECTION_NAME]

        query = {"timestamp": {"$exists": True}, "x": {"$exists": True}, "y": {"$exists": True}, "z": {"$exists": True}}
        for doc in collection.find(query).sort("timestamp", 1):
            print(f"{doc['timestamp']}\t{doc['x']}\t{doc['y']}\t{doc['z']}")

if __name__ == "__main__":
    export()
