from pymongo import MongoClient

def export():
    # Host CのIPアドレス
    client = MongoClient("mongodb://172.31.199.:27017/") 
    # 加速度が入ったデータベース名を指定．
    db = client["iot"]
    collection = db["accel_raw"]

    # データを古い順に取得して標準出力へ
    for doc in collection.find().sort("t", 1):
        print(f"{doc['t']}\t{doc['x']}\t{doc['y']}\t{doc['z']}")

if __name__ == "__main__":
    export()
