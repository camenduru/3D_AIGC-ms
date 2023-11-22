from datetime import datetime
import os
import time
import requests

from alibabacloud_tea_openapi.models import Config
from alibabacloud_xrengine20230313.client import Client
from alibabacloud_xrengine20230313.models import PopCreateObjectProjectRequest, PopListObjectProjectRequest, \
    PopVideoSaveSourceRequest, PopBuildObjectProjectRequest, AuthUserRequest, LoginModelScopeRequest, \
    PopListObjectCaseRequest, UpdateUserEmailRequest, PopObjectProjectDetailRequest, PopObjectRetrievalRequest, \
    PopObjectRetrievalUploadDataRequest


def setup(ak: str, sk: str, endpoint: str):
    config = Config(access_key_id=ak, access_key_secret=sk, endpoint=endpoint)
    client = Client(config)
    return client


def refresh_jwt(client: Client, jwt):
    return client.auth_user(AuthUserRequest(jwt_token=jwt))


def login(client: Client, userid):
    return client.login_model_scope(LoginModelScopeRequest(token=userid, type="MODEL_SCOPE"))


def update_user_email(client: Client, email, jwt):
    resp = client.update_user_email(UpdateUserEmailRequest(email=email, jwt_token=jwt))
    print("update email:", resp)
    return resp


def create_project(client: Client, jwt, share):
    """
    创建项目

    Args:
        client (Client): 客户端对象
        jwt: JWT令牌
        share (bool): 是否共享项目

    Returns:
        object: 创建的项目对象
    """
    request = PopCreateObjectProjectRequest(jwt_token=jwt,
                                            title=f"魔搭项目_{int(time.time())}",
                                            mode="source",
                                            biz_usage="faster_inverse_rendering",
                                            auto_build=True,
                                            custom_source="model_scope",
                                            recommend_status="AGREE_SHARE" if share else "DISAGREE_SHARE")
    return client.pop_create_object_project(request)


def list_projects(client: Client, jwt, size=5):
    """
        列出项目

        Args:
            client (Client): API客户端对象
            jwt (str): 用户令牌
            size: 数量

        Returns:
            PopListObjectProjectResponse: 列出项目的响应结果
    """
    request = PopListObjectProjectRequest(jwt_token=jwt,
                                          current=1,
                                          size=size,
                                          with_source=True,
                                          custom_source="model_scope",
                                          status="MAKING,MAKING_FAILED,MAKING_SUCCESS,VIEWABLE")
    return client.pop_list_object_project(request)


def upload_to_oss(access_id,
                  policy,
                  signature,
                  host,
                  file_path,
                  oss_dir,
                  expire):
    file_name = f"modelscope_{int(datetime.timestamp(datetime.now()))}" + (os.path.splitext(file_path)[1] or '.png')
    key = oss_dir + file_name
    params = dict()
    params["name"] = file_name
    params["key"] = key
    params["policy"] = policy
    params["OSSAccessKeyId"] = access_id
    params["success_action_status"] = "200"
    params["signature"] = signature
    params["expire"] = expire
    print(params)

    r = requests.post(f"https://{host}",
                      files={'file': open(file_path, 'rb')},
                      data=params)
    print("response:", r.status_code, r.content)

    return r.status_code == 200, f"oss://{host.split('.')[0]}/{key}"


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


def get_project_detail(client: Client, jwt, project_id):
    return client.pop_object_project_detail(PopObjectProjectDetailRequest(jwt_token=jwt, project_id=project_id))


def search_3d_objects(client: Client, jwt, input_type, query, image_path):
    if input_type == "图片搜索":
        source_type = "imageUrl"
        oss_policy_data = client.pop_object_retrieval_upload_data(
            PopObjectRetrievalUploadDataRequest(jwt_token=jwt)).body.data
        print("oss_policy: ", oss_policy_data)
        result = upload_to_oss(oss_policy_data.access_id,
                               oss_policy_data.policy,
                               oss_policy_data.signature,
                               oss_policy_data.host,
                               image_path,
                               oss_policy_data.dir,
                               oss_policy_data.expire)
        print("upload result: ", result)
        content = result[1]
    else:
        source_type = "textPrompt"
        content = query
    return client.pop_object_retrieval(
        PopObjectRetrievalRequest(jwt_token=jwt, source_type=source_type, content=content))


def parse_project_list(project_list):
    def parse_project(project):
        print("project", project)
        try:
            build_result_url = project.dataset.build_result_url
            glb_url = build_result_url.get("glbModel", None) if build_result_url else None
            return ProjectModel(
                id=project.id,
                title=project.title,
                cover_url=project.dataset.cover_url,
                model_url=project.dataset.model_url,
                preview_url=project.dataset.preview_url,
                status=project.status,
                glb_url=glb_url
            )
        except IndexError:
            return None

    return list(map(parse_project, project_list))


# define a ProjectModel class to store project info
class ProjectModel:
    def __init__(self, id, title, cover_url, model_url, preview_url, status, glb_url):
        self.id = id
        self.title = title
        self.cover_url = cover_url
        self.model_url = model_url
        self.preview_url = preview_url
        self.status = status
        self.glb_url = glb_url
