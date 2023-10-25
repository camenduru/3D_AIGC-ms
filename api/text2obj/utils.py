import base64
import json
import datetime
from api.text2obj.api import text2Substance , queryHistoryProjectList, queryText2ObjModelsDetail

# gradio button点击事件函数：提交prompt创建项目并启动构建
async def t2m_doTask(task, state, jwt):
    # print('base64:' + task)
    # task = base64.b64decode(task).decode()
    try:
        request = json.loads(task)
        print('[TEXT2OBJ_t2m_doTask] request:', str(request))
        prompt = request['prompts']
        _id = request['_id']
        result = await text2Substance(jwt, prompt)
        state["ids"][_id] = result
        return [state, state]
    except Exception as e:
        print('[TEXT2OBJ_t2m_doTask] error:', e)
        state["ids"][_id] = {"success": False, "id": None}
        return [state, state]

# 在页面加载时获取历史记录列表
def t2m_htmlloaded():
    return None

# 获取历史记录列表
def t2m_loadHistoryList(jwt):
    result = queryHistoryProjectList(jwt)
    return ["""<script id="text2objexpression">""" + json.dumps({"historyList": result}) + """</script>"""]

# 轮询生成中项目的生成状态
async def t2m_refreshModelsStatus(list, states):
    try:
        idList = []
        for model in list:
            if model["id"] is not None:
                idList.append(model["id"])
        if len(idList) != 0:
            result = queryText2ObjModelsDetail(idList)
            if (result is not None):
                for projectDetail in result:
                    status = projectDetail['status']
                    dataset = projectDetail['dataset']
                    modelId = projectDetail["id"]
                    if status == 'VIEWABLE' or (dataset["buildResultUrl"] is not None and "whiteModel" in dataset["buildResultUrl"]) or status == 'MAKING_FAILED':
                        states["details"][modelId] = {
                            "timestamp": str(datetime.datetime.now().time()),
                            "success": True,
                            "id": modelId,
                            "status": status,
                            "dataset": dataset
                        }
    except Exception as e:
        print('[TEXT2OBJ_t2m_refreshModelsStatus] error:', e)
    finally:
        # return ["""<script id="text2objoutputhtml">""" + json.dumps(t2m_stats) + """</script>""", None]
        return [states, states]

# 将数据写入output script中
def t2m_updateOutput(state_json):
    return ["""<script id="text2objoutputhtml">""" + json.dumps(state_json) + """</script>""", None]

