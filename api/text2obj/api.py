import time
import json

from alibabacloud_tea_openapi.models import Config
from alibabacloud_xrengine20230313.client import Client
from alibabacloud_xrengine20230313.models import PopCreateObjectGenerationProjectRequest, \
    PopBuildObjectGenerationProjectRequest, PopQueryObjectGenerationProjectDetailRequest, \
    PopBatchQueryObjectGenerationProjectStatusRequest, PopListObjectGenerationProjectRequest

from config.env import access_key_id, access_key_secret, api_endpoint

config = Config(access_key_id=access_key_id, access_key_secret=access_key_secret, endpoint=api_endpoint)
xr_client = Client(config)


async def text2Substance(jwt, prompt, biz_usage):
    try:
        create_request = PopCreateObjectGenerationProjectRequest(
            title=f'魔搭项目_{int(time.time())}',
            ext_info=json.dumps({
                "prompt": str(prompt),
            }),
            intro='',
            biz_usage=biz_usage or "text_to_obj",
            jwt_token=jwt
        )
        create_response = await xr_client.pop_create_object_generation_project_async(create_request)
        print('[TEXT2OBJ_text2Substance] create_response:', str(create_response))
        project_id = ''
        success = False
        if create_response.status_code == 200 and create_response.body.success is True:
            project_id = create_response.body.data.id
            build_response = await xr_client.pop_build_object_generation_project_async(
                PopBuildObjectGenerationProjectRequest(jwt_token=jwt, project_id=project_id))
            if build_response.status_code == 200 and build_response.body.success is True:
                success = True
                return {"success": True, "id": create_response.body.data.id}
            else:
                return {"success": False, "id": create_response.body.data.id, "code": build_response.body.code}
        else:
            return {"success": False, "id": None, "code": create_response.body.code}
    except Exception as e:
        print('[ TEXT2OBJ_text2Substance] error', str(e))
        return {"success": False, "id": None}


async def queryText2ObjModelDetail(id):
    try:
        request = PopQueryObjectGenerationProjectDetailRequest(project_id=id)
        result = (await xr_client.pop_query_object_generation_project_detail_async(request=request)).to_map()
        result = transformResponse(result)
        if result['statusCode'] == 200 and result["body"]['success'] is True:
            status = result['body']['data']['status']
            dataset = result['body']['data']['dataset']
            if status == 'VIEWABLE' or (dataset is not None and dataset['buildResultUrl']['whiteModel'] is not None):
                return {"timestamp": str(time.time()), "success": True, "id": id,
                        "status": result['body']['data']['status'], "ext": result["body"]['data']['ext'],
                        "dataset": result['body']['data']['dataset']}
            else:
                return None
        elif result['statusCode'] == 200 and result['body']['success'] is True and result['body']['data']['status'] == 'MAKING_FAILED':
            err = result['body']['data']['buildDetail']['errorMessage']
            if is_json(err) is False:
                err = '未知错误'
            return {"timestamp": str(time.time()), "success": False, "id": id, "err": err,
                    "dataset": "", "status": "MAKING_FAILED"}
        return None
    except Exception as e:
        print('[TEXT2OBJ_queryText2ObjModelDetail] error:', e)
        return None


def queryText2ObjModelsDetail(ids):
    ids = ','.join(ids)
    try:
        request = PopBatchQueryObjectGenerationProjectStatusRequest(project_ids=ids)
        result = xr_client.pop_batch_query_object_generation_project_status(request).to_map()
        result = transformResponse(result)
        if result["statusCode"] == 200 and result["body"]["success"] is True:
            return result["body"]["data"]
        else:
            print('[TEXT2OBJ_queryText2ObjModelsDetail] error:', result)
            return None
    except Exception as e:
        print('[TEXT2OBJ_queryText2ObjModelsDetail] error:', e)
        return None


def queryHistoryProjectList(jwt, current, size):
    try:
        request = PopListObjectGenerationProjectRequest(jwt_token=jwt, current=current, size=size)
        result = xr_client.pop_list_object_generation_project(request).to_map()
        result = transformResponse(result)
        print(f'[TEXT2OBJ_queryHistoryProjectList] result: {result}')
        if result['statusCode'] == 200 and result['body']['success'] is True:
            return {
                'total': result['body']['total'],
                'list': result['body']['data']
            }
        else:
            print(f'[TEXT2OBJ_queryHistoryProjectList] error: {result}', )
            return {
                'total': result['body']['total'],
                'list': []
            }
    except Exception as e:
        print(f'[TEXT2OBJ_queryHistoryProjectList] error: {e}')
        return {
            'total': 0,
            'list': []
        }


def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


def transformResponse(data):
    if isinstance(data, list):
        res = []
        for value in data:
            res.append(transformResponse(value))
        return res
    elif isinstance(data, dict):
        res = {str(key)[:1].lower() + str(key)[1:]: transformResponse(data[key]) for key in data}
        return res
    else:
        return data
