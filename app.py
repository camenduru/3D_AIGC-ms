import base64
import datetime
import json
from pathlib import Path

import gradio as gr

from api.api_manager import setup, list_projects, login, list_featured_projects, create_project_sts, action_post_upload, \
    update_user_email, get_project_detail, search_3d_objects, parse_project_list
from api.html_composer import single_model_viewer_iframe, project_video_constructor, project_list_html
from api.text2obj.utils import t2m_doTask, t2m_htmlloaded, t2m_refreshModelsStatus, t2m_updateOutput, \
    t2m_loadHistoryList
from config.env import access_key_id, access_key_secret, api_endpoint
from samples import *
from script import vite_js

# client = setup("ACSTQDkNtSMrZtwL", "zXJ7QF79Oz", "xrengine-daily.aliyuncs.com")
client = setup(access_key_id, access_key_secret, api_endpoint)

css = Path('style.css').read_text()
header_html = Path('htmls/header.html').read_text()
model_building_html = Path('htmls/model_building.html').read_text()
model_placeholder_html = Path("htmls/model_placeholder.html").read_text()
model_build_failed_html = Path('htmls/model_build_failed.html').read_text()
video_uploader_steps_html = Path('htmls/video_upload_steps.html').read_text()
model3d_label_html = Path("htmls/model3d_label.html").read_text()
tabbed_model_results_html = Path("htmls/tabbed_model_results.html").read_text()

app_js = Path("js/app.js").read_text()
upload_js = Path("js/upload.js").read_text()
app_post_load_js = Path("js/app_post_load.js").read_text()
hd_model_result_js = Path("js/hd_model_result.js").read_text()
project_item_click_js = Path("js/project_item_click.js").read_text()


def sample_data_on_select(evt: gr.SelectData):
    print(f"You selected {evt.value} at {evt.index} from {evt.target}")
    try:
        item = model_samples[evt.index]
        return [source_video.update(value=item["video"]),
                model_state_container.update(visible=False),
                remote_model_viewer.update(value=single_model_viewer_iframe(item["model"], None, item["name"], "inverse_rendering", False),
                                           visible=True)
                ]
    except IndexError:
        gr.Error("模型加载失败")


def upload_btn_on_click():
    return [
        source_video.update(value=None),
        model_state_container.update(visible=True),
        remote_model_viewer.update(visible=False)
    ]


def prepare_for_upload(jwt_token, share_check):
    print("share checked", share_check)
    result = create_project_sts(client, jwt_token, share_check)
    return upload_helper_txt.update(value=json.dumps(result))


async def upload_completion_btn_click(jwt_token, upload_txt):
    print("txt: ", upload_txt)
    project_id = json.loads(upload_txt)["proj_id"]
    success = action_post_upload(client, jwt_token, project_id)
    return projects_html.update(await fetch_project_list_to_html(jwt_token))


async def fetch_project_list_to_html(jwt_token):
    try:
        if not jwt_token:
            return []
        resp = await list_projects(client, jwt=jwt_token)
        print("list projects:", resp)

        def get_covers(proj):
            try:
                video_url = proj.source.source_files[0].url
                print("video url", video_url)
                if not video_url:
                    return ""
                else:
                    status = proj.status
                    if status == "VIEWABLE":
                        if proj.audit_status == "BLOCK":
                            status = "MAKING_FAILED"
                        elif proj.audit_status == "INNIT":
                            status = "MAKING"

                    glb_model_url = proj.dataset.build_result_url.get("glbModel", None)
                    video_cover_url = proj.source.source_files[0].cover_url

                    ext_info = json.loads(proj.ext) if proj.ext else None
                    print("project extra info: ", ext_info)
                    hd_project_id = ext_info.get("childIRId", None) if ext_info else None
                    fast_project_id = ext_info.get("childFIRId", None) if ext_info else None
                    return project_video_constructor(project_id=proj.id,
                                                     hd_project_id=hd_project_id,
                                                     fast_project_id=fast_project_id,
                                                     video_url=video_url,
                                                     video_cover_url=video_cover_url,
                                                     status=status,
                                                     model_url=proj.dataset.model_url,
                                                     glb_url=glb_model_url)
            except IndexError:
                return ""

        proj_videos = [item for item in list(map(get_covers, resp.body.data)) if item is not None]
        html = "<div style='display: flex'>" + "".join(proj_videos) + "</div>"
        return html
    except:
        raise gr.Error("获取数据失败，请刷新重试。")


def fetch_featured_projects_to_html(jwt_token):
    try:
        resp = list_featured_projects(client, jwt_token)
        print("featured projects:", resp)
        data = resp.body.data
        biz_usage = data[0].biz_usage if data else "inverse_rendering"
        return project_list_html(parse_project_list(data), biz_usage=biz_usage)
    except:
        raise gr.exceptions.Error("获取数据失败，请刷新重试。")


def update_email_btn_click(email_txt, jwt_token):
    print("new email", email_txt)
    print("jwt:", jwt_token)
    update_user_email(client, base64.b64encode(email_txt.encode()).decode("utf-8"), jwt_token)


def project_helper_btn_on_click(model_url_txt, glb_model_url_txt):
    print("model_url_txt: ", model_url_txt, "glb_model_url_txt: ", glb_model_url_txt)
    if model_url_txt:
        return [
            source_video.update(value=model_samples[0]["video"]),
            model_state_container.update(visible=False),
            remote_model_viewer.update(visible=True,
                                       value=single_model_viewer_iframe(model_url_txt,
                                                                        glb_model_url_txt,
                                                                        "",
                                                                        "inverse_rendering",
                                                                        True))
        ]
    else:
        return [
            source_video.update(value=model_samples[0]["video"]),
            model_state_container.update(visible=True),
            remote_model_viewer.update(visible=False, value="")
        ]


def update_fast_model_download_link(jwt_token, fast_project_id):
    if not fast_project_id:
        return
    resp = get_project_detail(client, jwt_token, fast_project_id)
    print("fast project detail", resp)
    if not resp.body.data:
        return
    glb_model_url = resp.body.data.dataset.build_result_url.get("glbModel", None)
    return download_helper_txt.update(value=glb_model_url)


def hd_model_result_tab_click(jwt, hd_project_id):
    print("jwt: ", jwt, "; hd_project_id: ", hd_project_id)
    if not hd_project_id:
        return
    resp = get_project_detail(client, jwt, hd_project_id)
    print("resp: ", resp)
    data = resp.body.data
    if not data:
        return
    project_status = data.status
    model_url = data.dataset.model_url
    glb_model_url = data.dataset.build_result_url.get("glbModel", None)
    result = {
        'status': project_status,
        'model_url': model_url,
        'name': data.title,
        'glb_url': glb_model_url
    }
    # convert `result` to json string
    return hd_helper_txt.update(json.dumps(result))


def update_usr_login(userInfo):
    userInfo = json.loads(userInfo)
    return [
        jwt_token_txt.update(userInfo['jwtToken']),
        usr_email_text.update(userInfo['email'])
    ]


def update_time():
    return str(datetime.datetime.now().time())


def search_btn_on_click(jwt_txt, input_type, txt, image):
    try:
        ret = search_3d_objects(client, jwt_txt, input_type, txt, image)
        print("search results: ", ret)
        text_error = "您输入的文本不符合要求，请重新输入"
        image_error = "您上传的图片不符合要求，请重新上传"
        if ret.body.code == "XR15110000000451":
            error_html = f"<span style='color: red;'>{text_error}</span>"
            return [
                search_results.update(value=project_list_html([], "")),
                search_error_label.update(visible=True, value=error_html)
            ]
        if ret.body.code == "XR15110000000454":
            error_html = f"<span style='color: red;'>{image_error}</span>"
            return [
                search_results.update(value=project_list_html([], "")),
                search_error_label.update(visible=True, value=error_html)
            ]
        return [
            search_results.update(value=project_list_html(ret.body.data, biz_usage="model_search")),
            search_error_label.update(visible=False)
        ]
    except:
        raise gr.exceptions.Error("搜索失败，请刷新重试。")


def search_input_changed(radio, image, txt):
    print("search text", txt, "; search image", image)
    if radio == "图片搜索":
        return [
            search_btn.update(interactive=(image is not None)),
            search_error_label.update(visible=False)
        ]
    else:
        return [
            search_btn.update(interactive=bool(txt.strip())),
            search_error_label.update(visible=False)
        ]


def search_type_radio_changed(radio, image, txt):
    if radio == "图片搜索":
        return [
            search_input_img.update(visible=True),
            search_input_txt.update(visible=False),
            search_btn.update(interactive=(image is not None)),
            search_error_label.update(visible=False)
        ]
    else:
        return [
            search_input_img.update(visible=False),
            search_input_txt.update(visible=True),
            search_btn.update(interactive=txt),
            search_error_label.update(visible=False)
        ]

# 在页面加载时获取历史记录列表
def app_post_load(jwt):
    print("app_post_load jwt: ", jwt)
    return featured_projects_html.update(value=fetch_featured_projects_to_html(jwt))

async def gr_on_load(uuid):
    print(f"Triggered fetch_uuid: {uuid}", flush=True)

    test_user_id = uuid #or "a28d98bc229cc31b26d226bae566cbb0"
    # NOTE: remove {test_user_id} and change to uuid when release
    if test_user_id:
        resp = login(client, test_user_id)
        print("login response: ", resp)
        try:
            jwt = resp.body.data.jwt_token
            email = resp.body.data.email
            return [
                uuid_txt.update(test_user_id),
                jwt_token_txt.update(jwt),
                usr_email_text.update(email),
                projects_html.update(value=await fetch_project_list_to_html(jwt))
            ]
        except (NameError, AttributeError):
            raise gr.exceptions.Error("用户登录失败，请刷新重试。")
    else:
        raise gr.exceptions.Error("用户登录失败，请刷新重试。")


with gr.Blocks(css=css) as demo:
    gr.HTML(header_html)
    uuid_txt = gr.Text(label="modelscope_uuid", elem_id="uuid", visible=False)
    jwt_token_txt = gr.Text(label="modelscope_jwt_token", elem_id="jwt_token", visible=False)
    with gr.Tab("文生3D", elem_id="t2m_tab"):
        t2m_expression = gr.HTML("""<script id="text2objexpression">""" + json.dumps({}) + """</script>""",
                                 visible=False)
        t2m_input = gr.HTML(elem_id="text2obj")
        t2m_button = gr.Button(elem_id="text2obj-button-hidden", visible=False)
        t2m_stats = gr.State(value={"ids": {}, "details": {}})
        t2m_output = gr.HTML(
            """<script id="text2objoutputhtml">""" + json.dumps({"ids": {}, "details": {}}) + """</script>""",
            visible=False)
        t2m_json = gr.JSON(visible=False)
        t2m_json.change(t2m_updateOutput, inputs=[t2m_json], outputs=[t2m_output])
        t2m_ticker = gr.Label(update_time, visible=False, every=1)
        t2m_ticker.change(t2m_refreshModelsStatus, inputs=[t2m_input, t2m_stats], outputs=[t2m_stats, t2m_json],
                          _js='''(i, s) => [window.getText2ObjMakingList(), s]''')

        t2m_button.click(t2m_doTask, _js='''(a, b, j) => [window.getText2ObjData(), b, j]''',
                         inputs=[t2m_input, t2m_stats, jwt_token_txt], outputs=[t2m_stats, t2m_json])
        t2m_js = vite_js()
        t2m_load_history_button = gr.Button(elem_id='text2obj-button-load-history', visible=False)
        t2m_load_history_button.click(t2m_loadHistoryList, inputs=[jwt_token_txt, t2m_stats, t2m_input],
                                      outputs=t2m_expression,
                                      _js='''(j, s, i) => [j, s, window.getText2ObjLoadHistoryParams()]''')
    with gr.Tab("视频生3D", elem_id="v2m_tab"):
        video_uploader_steps = gr.HTML(value=video_uploader_steps_html)
        with gr.Row():
            with gr.Column():
                upload_helper_txt = gr.Text(label="upload_helper", elem_id="upload_helper_txt", visible=False)
                usr_email_text = gr.Text(elem_id="user_email", visible=False)
                update_email_btn = gr.Button(elem_id="gr_update_email_btn", visible=False)
                share_checkbox = gr.Checkbox(False, label="同意分享至官方案例集", container=False,
                                             elem_id="gr_share_checkbox", visible=False)
                upload_helper_btn = gr.Button("生成模型", elem_id="upload_helper_btn", visible=False)
                upload_completion_btn = gr.Button(elem_id="upload_completion_btn", visible=False)
                download_helper_txt = gr.Text(elem_id="download_helper_txt", visible=False)
                hd_helper_txt = gr.Text(elem_id="hd_help_text", visible=False)
                hd_helper_btn = gr.Button(elem_id="hd_helper_button", visible=False)
                gr_login_button = gr.Button(elem_id="gr_login_button", visible=False)
                gr_login_button.click(update_usr_login, inputs=jwt_token_txt, outputs=[jwt_token_txt, usr_email_text],
                                      _js="""() => [window.getUserInfo()]""")

                source_video = gr.Video(label="源视频",
                                        height=500,
                                        interactive=False,
                                        autoplay=False,
                                        elem_id="video_input")
            with gr.Column(elem_id="model_viewer_area"):
                model_state_container = gr.HTML(label="模型结果",
                                                show_label=True,
                                                elem_id="model_state_container",
                                                value=model3d_label_html.join(
                                                    [model_placeholder_html, model_building_html,
                                                     model_build_failed_html]))
                remote_model_viewer = gr.HTML(label="模型结果",
                                              show_label=True,
                                              elem_id="model_viewer_container",
                                              visible=False)
                hd_helper_btn.click(fn=hd_model_result_tab_click,
                                    inputs=[jwt_token_txt, hd_helper_txt],
                                    outputs=hd_helper_txt,
                                    _js="""
                                        () => [document.querySelector('#jwt_token textarea').value, document.querySelector('.project_vid_container.selected').getAttribute('data-hd-project-id')]
                                    """) \
                    .then(fn=None, _js=hd_model_result_js)
        with gr.Row():
            with gr.Column():
                gr.HTML(value="<p>样例视频</p>",
                        elem_classes="section_title")
                example_videos = gr.Dataset(label="",
                                            samples=list(map(lambda x: [x["cover"]], model_samples)),
                                            components=[gr.Image(visible=False)],
                                            elem_id="example_videos",
                                            container=False)
            with gr.Column():
                gr.HTML(
                    value="<p>模型记录<span style='font-size:11px; color: #9ca3afcc; margin-left:6px;'>保留最近5个记录</span></p>",
                    elem_classes="section_title")
                project_helper_btn = gr.Button(elem_id="temp_btn", visible=False)
                projects_html = gr.HTML(elem_id="projects_container")
        with gr.Column():
            gr.HTML("<h2 style='text-align:center; margin-top: 20px;'>模型案例</h2>")
            featured_projects_html = gr.HTML(elem_id="featured_projects_container")

        # upload steps:
        # fn 1. disable upload button, reset model_state_container, remote_model_viewer
        # fn 2. create project, return ak sk sts as json to temp text
        # fn 3. js upload video, on completion, set temp text
        # fn 4. save source, build project, reload projects section and select the first one.

        upload_helper_btn.click(upload_btn_on_click,
                                outputs=[source_video, model_state_container, remote_model_viewer]) \
            .then(prepare_for_upload,
                  inputs=[jwt_token_txt, share_checkbox],
                  outputs=upload_helper_txt) \
            .then(fn=None,
                  inputs=upload_helper_txt,
                  outputs=[],
                  _js=upload_js)

        upload_completion_btn.click(fn=upload_completion_btn_click,
                                    inputs=[jwt_token_txt, upload_helper_txt],
                                    outputs=[projects_html]) \
            .then(fn=None,
                  _js=""" 
                    () => { document.querySelector(".project_vid_container").click() }
                  """)

        example_videos.select(sample_data_on_select,
                              outputs=[source_video, model_state_container, remote_model_viewer],
                              _js="""
                                () => {
                                    const example_videos = document.querySelector('#example_videos')
                                    example_videos.style.pointerEvents = "none"
                                    example_videos.style.opacity = 0.6
                                }
                              """) \
            .then(fn=None, _js="""
                () => {
                    const example_videos = document.querySelector('#example_videos')
                    example_videos.style.pointerEvents = 'all'
                    example_videos.style.opacity = 1
                }
            """)
        update_email_btn.click(update_email_btn_click,
                               inputs=[usr_email_text, jwt_token_txt],
                               _js="() => [document.querySelector('#user_email textarea').value, document.querySelector('#jwt_token textarea').value]")
        project_helper_btn.click(project_helper_btn_on_click,
                                 inputs=[project_helper_btn, project_helper_btn],
                                 outputs=[source_video, model_state_container, remote_model_viewer],
                                 _js="""
                                    () => {
                                    const selected_project = document.querySelector('.project_vid_container.selected')
                                    return [
                                        selected_project.getAttribute('data-model-url'),
                                        selected_project.getAttribute('data-glb-url')
                                     ]
                                    } 
                                 """) \
            .then(fn=update_fast_model_download_link,
                  inputs=[jwt_token_txt, download_helper_txt],
                  outputs=download_helper_txt,
                  _js="() => [document.querySelector('#jwt_token textarea').value, document.querySelector('.project_vid_container.selected').getAttribute('data-fast-project-id')] ") \
            .then(fn=None,
                  _js=project_item_click_js)
    with gr.Tab("3D模型检索 (未上线)", elem_id="model_search_tab"):
        with gr.Column():
            search_type_radio = gr.Radio(["图片搜索", "文本搜索"], value="图片搜索", show_label=False, container=False,
                                         elem_id="search_type_radio")
            with gr.Row():
                search_input_img = gr.Image(label="图片", elem_id="image_selector", show_label=False, type='filepath')
                # gr.HTML(value="<span style='font-size: 15px;'>或</span>", elem_id="or_label")
                search_input_txt = gr.Text(show_label=False, elem_id="search_input_txt", lines=3,
                                           info="输入一段3D模型的文字描述", placeholder="建议使用英文搜索",
                                           visible=False)
            search_error_label = gr.HTML(visible=False)
            search_btn = gr.Button(value="搜索3D模型", elem_id="search_btn", interactive=False)

            search_results_header = gr.HTML("<h2 style='text-align:center; margin-top: 20px;'>搜索结果</h2>")
            search_results = gr.HTML(elem_id="search_model3d_results")

        search_type_radio.change(search_type_radio_changed,
                                 inputs=[search_type_radio, search_input_img, search_input_txt],
                                 outputs=[search_input_img, search_input_txt, search_btn, search_error_label])
        search_input_img.clear(fn=None, _js="""
            () => { image_selector_placeholder() }
        """)
        search_input_img.change(search_input_changed, inputs=[search_type_radio, search_input_img, search_input_txt],
                                outputs=[search_btn, search_error_label])
        search_input_txt.change(search_input_changed, inputs=[search_type_radio, search_input_img, search_input_txt],
                                outputs=[search_btn, search_error_label])
        search_btn.click(search_btn_on_click,
                         inputs=[jwt_token_txt, search_type_radio, search_input_txt, search_input_img],
                         outputs=[search_results, search_error_label])

    demo.load(fn=gr_on_load,
              inputs=uuid_txt,
              outputs=[
                  uuid_txt,
                  jwt_token_txt,
                  usr_email_text,
                  projects_html
              ],
              _js=app_js) \
        .then(fn=None,
              _js=app_post_load_js)
    demo.load(fn=t2m_htmlloaded, _js=t2m_js).then(fn=app_post_load, inputs=jwt_token_txt, outputs=[featured_projects_html])

demo.queue(concurrency_count=300)
demo.launch()