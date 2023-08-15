import os
import time

import oss2
import requests
from alibabacloud_tea_openapi.models import Config
from alibabacloud_xrengine20230313.client import Client
from alibabacloud_xrengine20230313.models import PopCreateObjectProjectRequest, PopListObjectProjectRequest, \
    PopVideoSaveSourceRequest, PopBuildObjectProjectRequest, AuthUserRequest, LoginModelScopeRequest, \
    PopListObjectCaseRequest


# ID [2023-07-12 10:43:36] Triggered fetch_uuid: a28d98c229cc31b26d226bae566cbb0

def setup(ak: str, sk: str, endpoint: str):
    config = Config(access_key_id=ak, access_key_secret=sk, endpoint=endpoint)
    client = Client(config)
    return client


def refresh_jwt(client: Client, jwt):
    return client.auth_user(AuthUserRequest(jwt_token=jwt))


def login(client: Client, userid):
    return client.login_model_scope(LoginModelScopeRequest(token=userid, type="MODEL_SCOPE"))


def create_project(client: Client, jwt, share):
    request = PopCreateObjectProjectRequest(jwt_token=jwt,
                                            title=f"魔搭项目_{int(time.time())}",
                                            mode="source",
                                            biz_usage="faster_inverse_rendering",
                                            auto_build=True,
                                            custom_source="model_scope",
                                            recommend_status="AGREE_SHARE" if share else "DISAGREE_SHARE")
    return client.pop_create_object_project(request)


def list_projects(client: Client, jwt):
    # biz_usage = "inverse_rendering",
    request = PopListObjectProjectRequest(jwt_token=jwt,
                                          current=1,
                                          size=5,
                                          with_source=True,
                                          custom_source="model_scope",
                                          status="MAKING,MAKING_FAILED,MAKING_SUCCESS,VIEWABLE")
    return client.pop_list_object_project(request)


# def upload_to_oss(client,
#                   project_id,
#                   access_id,
#                   policy,
#                   signature,
#                   host,
#                   file_path,
#                   oss_dir,
#                   expire,
#                   progress_callback):
#     file_name = os.path.basename(file_path)
#     key = oss_dir + "videos/" + file_name
#     params = dict()
#     params["name"] = file_name
#     params["key"] = key
#     params["policy"] = policy
#     params["OSSAccessKeyId"] = access_id
#     params["success_action_status"] = "200"
#     params["signature"] = signature
#     params["expire"] = expire
#     params["x-oss-meta-env"] = "production"
#     print(params)
#
#     r = requests.post(f"https://{host}",
#                       files={'file': open(file_path, 'rb')},
#                       data=params)
#     print("response:", r.status_code, r.content)
#
#     if r.status_code == 200:
#         print(f'uploaded success: {key}.')
#         client.pop_video_save_source(PopVideoSaveSourceRequest(project_id=project_id, source_type="VID"))
#         ret = client.pop_build_object_project(PopBuildObjectProjectRequest(project_id=project_id))
#         return ret.body.success
#     return False


def create_project_sts(client: Client, jwt, share):
    c_resp = create_project(client, jwt, share)
    print("create_project response: ", c_resp)
    project_id = c_resp.body.data.id
    sts_token = c_resp.body.data.source.token
    params = dict()
    params["ak"] = sts_token.access_key_id
    params["sk"] = sts_token.access_key_secret
    params["sts"] = sts_token.security_token
    bucket = sts_token.host.split(".")[0]
    params["bucket"] = bucket
    params["endpoint"] = sts_token.host.replace(f"{bucket}.", "")
    params["region"] = sts_token.host.split(".")[1]
    params["proj_id"] = project_id
    params["key"] = sts_token.dir + "videos/"
    params["expire"] = sts_token.expiration
    return params

#
# def create_then_upload(client: Client, jwt, share, video_path, progress_callback):
#     c_resp = create_project(client, jwt, share)
#     print("create_project response: ", c_resp)
#     project_id = c_resp.body.data.id
#     sts_token = c_resp.body.data.source.token
#     auth = oss2.StsAuth(sts_token.access_key_id, sts_token.access_key_secret, sts_token.security_token)
#
#     bucket = sts_token.host.split(".")[0]
#     endpoint = sts_token.host.replace(f"{bucket}.", "")
#     print("endpoint:", endpoint, ", bucket:", bucket)
#     bucket = oss2.Bucket(auth, endpoint, bucket)
#
#     file_name = os.path.basename(video_path)
#     key = sts_token.dir + "videos/" + file_name
#     # 上传文件。
#     # 如果需要在上传文件时设置文件存储类型（x-oss-storage-class）和访问权限（x-oss-object-acl），请在put_object中设置相关Header。
#     headers = dict()
#     headers["name"] = file_name
#     headers["key"] = key
#     headers["success_action_status"] = "200"
#     headers["expire"] = sts_token.expiration
#
#     ret = bucket.put_object_from_file(key=key,
#                                       filename=video_path,
#                                       headers=headers,
#                                       progress_callback=progress_callback)
#     if ret.status == 200:
#         save_source = client.pop_video_save_source(PopVideoSaveSourceRequest(project_id=project_id, source_type="VID"))
#         print("save source: ", save_source)
#         ret = client.pop_build_object_project(PopBuildObjectProjectRequest(project_id=project_id))
#         print("build project: ", ret)
#         return ret.body.success


def action_post_upload(client: Client, jwt, project_id):
    save_source = client.pop_video_save_source(PopVideoSaveSourceRequest(project_id=project_id, source_type="VID"))
    print("save source: ", save_source)
    ret = client.pop_build_object_project(PopBuildObjectProjectRequest(project_id=project_id))
    print("build project: ", ret)
    return ret.body.success

def list_featured_projects(client: Client, jwt):
    return client.pop_list_object_case(PopListObjectCaseRequest(jwt_token=jwt, size=12))
