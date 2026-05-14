# IoT 加速度センサ データ収集・分類システム

Spresense の加速度センサ (KX126) から取得した3軸データを MongoDB に蓄積し、MapReduce で STILL / WALK / RUN に分類・可視化するシステム。

---

## システム構成

```
Spresense ──Serial──> Host A ──SSH tunnel──> MongoDB (Host C)
                                                   │
                                              Host B (MapReduce + 可視化)
```

詳細は [`docs/overview.md`](docs/overview.md) を参照。

---

## ディレクトリ構成

```
final/
├── arduino/sender/     Spresense スケッチ (KX126 常時送信)
├── raspi/              Host A — シリアル受信・MongoDB アップロード
├── server/             共通ユーティリティ (CSV → JSON 変換)
├── hostB/              Host B — MapReduce・可視化
├── check_db.py         デバッグ用 DB 確認ツール
├── docs/               設計書・仕様書
└── test/               テストデータ
```

---

## セットアップ

```bash
pip install pyserial pymongo "paramiko<3" sshtunnel matplotlib
```

---

## 実行方法

### Host A（データ収集）

```bash
# シリアル受信（COMポートは環境に合わせる）
python3 raspi/receiver.py --port COM7

# CSV → MongoDB アップロード（別ターミナル）
python3 raspi/uploader.py --logs logs/
```

### Host B（分類・可視化）

```bash
python3 hostB/exporter.py | python3 hostB/mapper.py | sort | python3 hostB/reducer.py | python3 hostB/visualize.py
```

### デバッグ

```bash
python3 check_db.py               # 件数確認・最新10件表示
python3 check_db.py --out out.json  # 全件を JSON に出力
```
