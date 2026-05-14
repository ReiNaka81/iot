# ftp_server.py
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
import os


authorizer = DummyAuthorizer()
authorizer.add_user("user", "password", "./logs", perm="elradfmw")

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("0.0.0.0", 2121), handler)

print("FTPサーバ起動")
server.serve_forever()
