import datetime
import json

from alibabacloud_tea_openapi.models import Config
from alibabacloud_xrengine20230313.client import Client
from alibabacloud_xrengine20230313.models import PopCreateObjectGenerationProjectRequest, \
    PopBuildObjectGenerationProjectRequest, PopQueryObjectGenerationProjectDetailRequest, \
    PopBatchQueryObjectGenerationProjectStatusRequest, PopListObjectGenerationProjectRequest

from config.env import access_key_id, access_key_secret, api_endpoint

config = Config(access_key_id=access_key_id, access_key_secret=access_key_secret, endpoint=api_endpoint)
xr_client = Client(config)


async def text2Substance(jwt, prompt):
    try:
        create_request = PopCreateObjectGenerationProjectRequest().from_map({
            "Title": '魔搭项目' + str(datetime.datetime.now().time()),
            "ExtInfo": json.dumps({
                "prompt": str(prompt),
            }),
            "Intro": '',
            "JwtToken": jwt
        })
        create_response = await xr_client.pop_create_object_generation_project_async(create_request)
        print('[TEXT2OBJ_text2Substance] create_response:', str(create_response))
        project_id = ''
        success = False
        if create_response.status_code == 200 and create_response.body.success is True:
            project_id = create_response.body.data.id
            build_response = await xr_client.pop_build_object_generation_project_async(
                PopBuildObjectGenerationProjectRequest().from_map({"JwtToken": jwt, "ProjectId": project_id}))
            if (build_response.status_code == 200 and build_response.body.success is True):
                success = True
                return {"success": True, "id": create_response.body.data.id}
    except Exception as e:
        print('[ TEXT2OBJ_text2Substance] error', str(e))
    finally:
        if not success:
            return {"success": False, "id": None}


async def queryText2ObjModelDetail(id):
    try:
        result = (await xr_client.pop_query_object_generation_project_detail_async(
            PopQueryObjectGenerationProjectDetailRequest().from_map({"ProjectId": id}))).to_map()
        result = transformResponse(result)
        if result['statusCode'] == 200 and result["body"]['success'] is True:
            status = result['body']['data']['status']
            dataset = result['body']['data']['dataset']
            if (status == 'VIEWABLE' or (dataset is not None and dataset['buildResultUrl']['whiteModel'] is not None)):
                return {"timestamp": str(datetime.datetime.now().time()), "success": True, "id": id,
                        "status": result['body']['data']['status'], "ext": result["body"]['data']['ext'],
                        "dataset": result['body']['data']['dataset']}
            else:
                return None
        elif result['statusCode'] == 200 and result['body']['success'] is True and result['body']['data']['status'] == 'MAKING_FAILED':
            err = result['body']['data']['buildDetail']['errorMessage']
            if is_json(err) is False:
                err = '未知错误'
            return {"timestamp": str(datetime.datetime.now().time()), "success": False, "id": id, "err": err,
                    "dataset": "", "status": "MAKING_FAILED"}
        return None
    except Exception as e:
        print('[TEXT2OBJ_queryText2ObjModelDetail] error:', e)
        return None


def queryText2ObjModelsDetail(ids):
    ids = ','.join(ids)
    try:
        result = (xr_client.pop_batch_query_object_generation_project_status(
            PopBatchQueryObjectGenerationProjectStatusRequest().from_map({"ProjectIds": ids}))).to_map()
        result = transformResponse(result)
        if (result["statusCode"] == 200 and result["body"]["success"] is True):
            return result["body"]["data"]
        else:
            print('[TEXT2OBJ_queryText2ObjModelsDetail] error:', result)
            return None
    except Exception as e:
        print('[TEXT2OBJ_queryText2ObjModelsDetail] error:', e)
        return None


def queryHistoryProjectList(jwt, current, size):
    try:
        result = xr_client.pop_list_object_generation_project(PopListObjectGenerationProjectRequest().from_map(
            {"JwtToken": jwt, "Current": current, "Size": size})).to_map()
        result = transformResponse(result)
        print(f'[TEXT2OBJ_queryHistoryProjectList] result: {result}')
        if (result['statusCode'] == 200 and result['body']['success'] is True):
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
