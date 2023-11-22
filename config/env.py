import base64
import json
import os


# define an object class with ak, sk and endpoint
class Env:
    def __init__(self, ak, sk, endpoint):
        self.ak = ak
        self.sk = sk
        self.endpoint = endpoint


current_env = Env(ak="", sk="", endpoint="xrengine.cn-hangzhou.aliyuncs.com")
try:
    with open("config/env_list.json") as json_file:
        json_data = json.load(json_file)
        print(json_data)
        env = json_data["pre"]  # daily, pre, prod
        current_env = Env(ak=env["ak"], sk=env["sk"], endpoint=env["endpoint"])
except OSError:
    print("Error: No such file or directory")

access_key_id = base64.b64decode(os.getenv("Var1", "")).decode("utf-8") or current_env.ak
access_key_secret = base64.b64decode(os.getenv("Var2", "")).decode("utf-8") or current_env.sk
api_endpoint = current_env.endpoint
