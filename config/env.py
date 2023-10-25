from Crypto.Cipher import AES
import base64
import os

# daily
# ak = "ACSTQDkNtSMrZtwL"
# sk = "zXJ7QF79Oz"
# endpoint = "xrengine-daily.aliyuncs.com"

#pre

# prod
ak = "LTAI5tBseK5tDfu4FJvGEQRZ"
sk = "4RIGB8psCJmRr6h1PY4uedikML95UZ"
endpoint = "xrengine.cn-hangzhou.aliyuncs.com"

access_key_id = base64.b64decode(os.getenv("Var1", "")).decode("utf-8") or ak
access_key_secret = base64.b64decode(os.getenv("Var2", "")).decode("utf-8") or sk
api_endpoint = endpoint