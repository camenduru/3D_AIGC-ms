from Crypto.Cipher import AES
import base64
import os

access_key_id = base64.b64decode(os.getenv("Var1", "")).decode("utf-8")
access_key_secret = base64.b64decode(os.getenv("Var2", "")).decode("utf-8")
api_endpoint = "xrengine.cn-hangzhou.aliyuncs.com"