"""
ftp.py (FTP サーバ)
Host A からアップロードされた .json ファイルを ./logs に受信する。
同じディレクトリを ingest.py が監視し、MongoDB へ投入する。

実行:
    python3 ftp.py
"""
import os

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

LOGS_DIR = "./logs"
PORT = 2121
USER = "user"
PASSWORD = "password"


def main():
    os.makedirs(LOGS_DIR, exist_ok=True)
    abs_dir = os.path.abspath(LOGS_DIR)

    authorizer = DummyAuthorizer()
    # e=入室 l=一覧 r=取得 a=追記 d=削除 f=リネーム m=mkdir w=書込
    authorizer.add_user(USER, PASSWORD, abs_dir, perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    server = FTPServer(("0.0.0.0", PORT), handler)
    print(f"FTPサーバ起動: 0.0.0.0:{PORT}  ルート={abs_dir}")
    print("Ctrl+C で停止")
    server.serve_forever()


if __name__ == "__main__":
    main()
