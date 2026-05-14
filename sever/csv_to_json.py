"""
csv_to_json.py
加速度CSV (timestamp, x, y, z) を JSON に変換する。

使い方:
    python3 csv_to_json.py input.csv                 # → input.json (配列形式)
    python3 csv_to_json.py input.csv -o out.json     # 出力先指定
    python3 csv_to_json.py input.csv --jsonl         # JSON Lines (mongoimport向き)
    python3 csv_to_json.py *.csv --out-dir json/     # 複数ファイルをまとめて変換
"""
import argparse
import csv
import glob
import json
import os
import sys


def csv_to_docs(in_path: str) -> list:
    """CSV (timestamp,x,y,z) を読み、各行を dict のリストとして返す。"""
    docs = []
    with open(in_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                docs.append({
                    "timestamp": row["timestamp"],
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "z": float(row["z"]),
                })
            except (KeyError, ValueError) as e:
                print(f"# skip row in {in_path}: {e}", file=sys.stderr)
    return docs


def convert(in_path: str, out_path: str, jsonl: bool) -> int:
    docs = csv_to_docs(in_path)
    with open(out_path, "w") as f:
        if jsonl:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        else:
            json.dump(docs, f, ensure_ascii=False, indent=2)
    return len(docs)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="入力CSV (glob可)")
    p.add_argument("-o", "--output", help="出力ファイル (単一入力時のみ)")
    p.add_argument("--out-dir", help="出力ディレクトリ (複数入力時)")
    p.add_argument("--jsonl", action="store_true",
                   help="JSON Lines 形式で出力 (mongoimport 向き)")
    return p.parse_args()


def main():
    args = parse_args()

    paths = []
    for pat in args.inputs:
        matched = glob.glob(pat)
        paths.extend(matched if matched else [pat])

    if not paths:
        print("入力ファイルが見つかりません", file=sys.stderr)
        sys.exit(1)

    ext = ".jsonl" if args.jsonl else ".json"

    for p in paths:
        if args.output and len(paths) == 1:
            out = args.output
        elif args.out_dir:
            os.makedirs(args.out_dir, exist_ok=True)
            stem = os.path.splitext(os.path.basename(p))[0]
            out = os.path.join(args.out_dir, stem + ext)
        else:
            out = os.path.splitext(p)[0] + ext

        n = convert(p, out, args.jsonl)
        print(f"{p} -> {out} ({n} rows)")


if __name__ == "__main__":
    main()
