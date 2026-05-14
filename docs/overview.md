# システム概要

## 1. 全体アーキテクチャ

```
+-----------+   Serial(USB)   +-------------------+   SSH tunnel   +-----------+
| Spresense | -------------> |  Host A (raspi/)  | ------------> |  Host C   |
| (KX126)   |   x,y,z @20Hz  | receiver.py       |  pymongo      |  MongoDB  |
|           |                | uploader.py       |  insert_many  |  iot.accel|
+-----------+                +-------------------+               |  _raw     |
                                                                 +-----------+
                                                                       |
                                                                       | query
                                                                       v
                                                                 +-----------+
                                                                 |  Host B   |
                                                                 | exporter  |
                                                                 | mapper    |
                                                                 | reducer   |
                                                                 | visualize |
                                                                 +-----------+
```

| ホスト | 役割 |
|--------|------|
| Spresense | KX126 加速度センサから x,y,z を 20Hz でシリアル送信 |
| Host A | シリアル受信・CSV化・MongoDB へ直接 insert |
| Host C | MongoDB サーバ（SSHトンネル越しにアクセス） |
| Host B | MongoDB からデータ取得・MapReduce・可視化 |

---

## 2. データフロー

```
Spresense
  │ x,y,z (Serial 115200bps, 20Hz)
  ▼
receiver.py        10秒ごとに CSV ファイルを ./logs に書き出す
  │ accel_YYYYMMDD_HHMMSS.csv
  ▼
uploader.py        CSV を発見次第 JSON に変換し MongoDB へ insert_many
  │ SSH tunnel (133.19.7.2:22 → 192.168.1.4:59501)
  ▼
MongoDB            DB: iot / Collection: accel_raw
  │ {"timestamp": "...", "x": 0.02, "y": 0.10, "z": 1.04}
  ▼
exporter.py        SSH tunnel 経由で全ドキュメントを timestamp 昇順で取得
  │ timestamp\tx\ty\tz (タブ区切り)
  ▼
mapper.py          ノルム = sqrt(x²+y²+z²) を計算、1秒単位の時間窓キーを付与
  │ window\tnorm
  ▼
sort               窓キーでソート（reducer が groupby できるようにする）
  │
  ▼
reducer.py         窓ごとにノルムの分散を計算し STILL/WALK/RUN に分類
  │ Time Window | Variance | State
  ▼
visualize.py       分散値の時系列グラフを描画
```

---

## 3. 分類アルゴリズム

| 分散値 (ノルムの分散) | 状態 |
|----------------------|------|
| < 0.01 | STILL（静止）|
| 0.01 〜 0.3 | WALK（歩行）|
| ≥ 0.3 | RUN（走行）|

- **ノルム**: `sqrt(x² + y² + z²)` — 3軸合成の加速度の大きさ
- **時間窓**: 1秒単位（タイムスタンプのミリ秒以下を切り捨て）
- 静止時は重力のみ（z ≈ 1.0G）でノルムがほぼ一定 → 分散ほぼ0

---

## 4. ファイル責務

```
final/
├── arduino/sender/
│   ├── sender.ino        Spresense メインスケッチ。20Hz でシリアル送信
│   ├── KX126.cpp         KX126 加速度センサドライバ
│   └── KX126.h
│
├── raspi/
│   ├── receiver.py       シリアル受信 → 10秒ごとに CSV を ./logs に書き出す
│   └── uploader.py       ./logs の CSV を監視 → JSON 変換 → MongoDB insert
│
├── server/
│   └── csv_to_json.py    CSV ファイルを dict のリストに変換するユーティリティ
│                         （uploader.py から import して使用）
│
├── hostB/
│   ├── exporter.py       MongoDB から全データを取得し タブ区切りで stdout に出力
│   ├── mapper.py         ノルム計算 + 時間窓キー付与
│   ├── reducer.py        窓ごとの分散計算 + STILL/WALK/RUN 分類
│   └── visualize.py      reducer の出力を受け取りグラフを描画
│
├── check_db.py           デバッグ用。DB の件数確認・全件 JSON エクスポート
├── img/plot.png          可視化結果
├── docs/
│   ├── overview.md       このファイル
│   ├── design.md         設計ドキュメント（詳細）
│   └── interface.md      Host A ↔ サーバ間インタフェース仕様
└── test/                 テストデータ
```

---

## 5. 接続情報

| 項目 | 値 |
|------|----|
| SSH ホスト | `133.19.7.2:22` |
| SSH ユーザ | `iot` |
| MongoDB ホスト | `192.168.1.4:59501`（SSH トンネル越し） |
| DB 名 | `iot` |
| Collection | `accel_raw` |

---

## 6. 実行方法

### Host A（ラズパイ側）

```bash
# シリアル受信（COMポートは環境に合わせる）
python3 raspi/receiver.py --port COM7

# CSV → MongoDB アップロード（別ターミナル）
python3 raspi/uploader.py --logs logs/
```

### Host B（可視化）

```bash
python3 hostB/exporter.py | python3 hostB/mapper.py | sort | python3 hostB/reducer.py | python3 hostB/visualize.py
```

### デバッグ

```bash
# DB の件数確認・最新10件表示
python3 check_db.py

# 全件を JSON ファイルに出力
python3 check_db.py --out output.json
```

---

## 7. 依存パッケージ

```bash
pip install pyserial pymongo "paramiko<3" sshtunnel matplotlib
```
