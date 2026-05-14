# Host B: 行動解析・可視化モジュール

このフォルダには、MongoDBからデータを抽出し、MapReduceを用いて行動（静止・歩行・走行）を判定・描画するコードが含まれています。

## ファイル構成
- `exporter6.py`: Host C (MongoDB) から生データを抽出
- `mapper6.py`: 加速度のノルム計算
- `reducer6.py`: 分散計算と行動判定
- `visualize.py`: 解析結果のグラフ表示
- `test.json`: 動作確認用のテストデータ

## 実行方法
### 1. ライブラリのインストール
pip install -r requirements.txt

### 2. 本番実行（MongoDB接続時）
python exporter6.py | python mapper6.py | sort | python reducer6.py | python visualize.py
