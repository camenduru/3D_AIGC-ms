import base64
import json
import os
from pathlib import Path
from urllib.parse import quote

import gradio as gr

from api_manager import setup, list_projects, login, list_featured_projects, create_project_sts, action_post_upload, update_user_email
from samples import samples

access_key_id = base64.b64decode(os.getenv("Var1", "")).decode("utf-8")
access_key_secret = base64.b64decode(os.getenv("Var2", "")).decode("utf-8")
api_endpoint = "xrengine.cn-hangzhou.aliyuncs.com"

client = setup(access_key_id, access_key_secret, api_endpoint)

css = Path('style.css').read_text()
header_html = Path('htmls/header.html').read_text()
model_building_html = Path('htmls/model_building.html').read_text()
model_placeholder_html = Path("htmls/model_placeholder.html").read_text()
model_build_failed_html = Path('htmls/model_build_failed.html').read_text()
video_uploader_steps_html = Path('htmls/video_upload_steps.html').read_text()
model3d_label_html = Path("htmls/model3d_label.html").read_text()
model3d_actions_html = Path("htmls/model3d_actions.html").read_text()

app_js = Path("app.js").read_text()
upload_js = Path("upload.js").read_text()

def model_preview_url(url, title):
    if not url:
        return ""
    return f"https://market.wapa.taobao.com/app/xr-paas/xr-paas-portal/index.html#/h5-modelviewer?modelUrl={quote(url)}&modelName={quote(title)}&bizUsage=inverse_rendering"

def model_viewer_iframe(url, title, show_actions: bool):
    model_iframe = f"""
    {model3d_label_html}
    <iframe class='model_container' src ='{model_preview_url(url, title)}'></iframe>
    """
    if show_actions:
        model_iframe = model3d_actions_html + model_iframe
    return model_iframe

def project_video_constructor(video_url, status, model_url, glb_url):
    if status == "CREATED":
        actual = "空项目"
        color = "white"
    elif status == "VIEWABLE":
        actual = "可预览"
        color = "green"
    elif status == "MAKING_FAILED":
        actual = "生成失败"
        color = "#FE5967"
    else:
        actual = "生成中"
        color = "white"

    actual_model_url = model_url if status == "VIEWABLE" else ""
    full_video_url = f"https:{video_url}"
    display_status = "display: none" if status == "VIEWABLE" else "display: block"
    actual_glb_url = glb_url if status == "VIEWABLE" else ""
    return f"""
        <div class='project_vid_container' data-model-url='{actual_model_url}' data-glb-url='{actual_glb_url}' data-status='{status}' onclick='project_video_on_click(this)'>
            <div class='project_status_overlay' style='{display_status}'>
                <p style='text-align: center; color: {color}; font-size: 16px; margin: 40% 0;'>{actual}</p>
            </div>
            <video class='project_vid' muted preload='auto' onmouseover='this.play()' onmouseout='this.pause()' src='{full_video_url}'></video>
        </div>
    """

def sample_data_on_select(evt: gr.SelectData):
    print(f"You selected {evt.value} at {evt.index} from {evt.target}")
    try:
        item = samples[evt.index]
        return [source_video.update(value=item["video"]),
                model_state_container.update(visible=False),
                remote_model_viewer.update(value=model_viewer_iframe(item["model"], item["name"], False),
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


def upload_completion_btn_click(jwt_token, upload_txt):
    print("txt: ", upload_txt)
    project_id = json.loads(upload_txt)["proj_id"]
    success = action_post_upload(client, jwt_token, project_id)
    return projects_html.update(project_list_html_constructor(jwt_token))

def fetch_project_list(jwt_token):
    try:
        if not jwt_token:
            return []
        resp = list_projects(client, jwt=jwt_token)
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
                    return project_video_constructor(video_url, status, proj.dataset.model_url, glb_model_url)
            except IndexError:
                return ""

        # images = list(map(get_covers, resp.body.data))
        proj_videos = [item for item in list(map(get_covers, resp.body.data)) if item is not None]
        return proj_videos
    except:
        raise gr.Error("获取数据失败，请刷新重试。")

def project_list_html_constructor(jwt_token):
    html = "<div style='display: flex'>" + "".join(fetch_project_list(jwt_token)) + "</div>"
    return html

def featured_projects_html_constructor(jwt_token):
    try:
        resp = list_featured_projects(client, jwt_token)
        print("featured projects:", resp)

        def get_model_url(proj):
            try:
                preview_url = proj.dataset.preview_url
                if not preview_url:
                    return None
                else:
                    return f"<a style='display: contents;' href='{model_preview_url(proj.dataset.model_url, proj.title)}' target='_blank'><video class='featured_model_vid' muted preload='auto' onmouseover='this.play()' onmouseout='this.pause()' src='{preview_url}'></video></a>"
            except IndexError:
                return None
        proj_model_htmls = [item for item in list(map(get_model_url, resp.body.data)) if item is not None]
        css_classes = "featured_model_list_container center_for_one" if len(proj_model_htmls) == 1 else "featured_model_list_container"
        return f"<div style='display: block;'><div class='{css_classes}'>" + "".join(proj_model_htmls) + "</div></div>"
    except:
        raise gr.exceptions.Error("获取数据失败，请刷新重试。")

def update_email_btn_click(email_txt, jwt_token):
    print("new email", email_txt)
    print("jwt:", jwt_token)
    update_user_email(client, base64.b64encode(email_txt.encode()).decode("utf-8"), jwt_token)

def temp_btn_on_click(model_url_txt):
    print("model_url_txt: ", model_url_txt)
    if model_url_txt:
        return [source_video.update(value="resource/guide.mp4"),
                model_state_container.update(visible=False),
                remote_model_viewer.update(visible=True, value=model_viewer_iframe(model_url_txt, "", True))
                ]
    else:
        return [
            source_video.update(value="resource/guide.mp4"),
            model_state_container.update(visible=True),
            remote_model_viewer.update(visible=False, value="")
        ]


def gr_on_load(uuid):
    print(f"Triggered fetch_uuid: {uuid}", flush=True)

    test_user_id = uuid
    # NOTE: remove {test_user_id} and change to uuid when release
    if test_user_id:
        resp = login(client, test_user_id)
        print("login response: ", resp)
        try:
            jwt = resp.body.data.jwt_token
            email = "" #resp.body.data.email
            return [jwt_token_txt.update(jwt),
                    usr_email_text.update(email),
                    projects_html.update(value=project_list_html_constructor(jwt)),
                    featured_projects_html.update(value=featured_projects_html_constructor(jwt))
                    ]
        except (NameError, AttributeError):
            raise gr.exceptions.Error("用户登录失败，请刷新重试。")
    else:
        raise gr.exceptions.Error("用户登录失败，请刷新重试。")


with gr.Blocks(css=css) as demo:
    gr.HTML(header_html)
    with gr.Tab("视频生成"):
        video_uploader_steps = gr.HTML(value=video_uploader_steps_html)
        with gr.Row():
            with gr.Column():
                uuid_txt = gr.Text(label="modelscope_uuid", visible=False)
                jwt_token_txt = gr.Text(label="modelscope_jwt_token", elem_id="jwt_token", visible=False)
                upload_helper_txt = gr.Text(label="upload_helper", elem_id="upload_helper_txt", visible=False)
                usr_email_text = gr.Text(elem_id="user_email", visible=False)
                update_email_btn = gr.Button(elem_id="gr_update_email_btn", visible=False)
                share_checkbox = gr.Checkbox(False, label="同意分享至官方案例集", container=False, elem_id="gr_share_checkbox", visible=False)
                upload_helper_btn = gr.Button("生成模型", elem_id="upload_helper_btn", visible=False)
                upload_completion_btn = gr.Button(elem_id="upload_completion_btn", visible=False)

                source_video = gr.Video(label="源视频",
                                        height=500,
                                        interactive=False,
                                        autoplay=True,
                                        elem_id="video_input")
            with gr.Column():
                model_state_container = gr.HTML(label="模型结果",
                                                show_label=True,
                                                elem_id="model_state_container",
                                                value=model3d_label_html.join([model_placeholder_html, model_building_html, model_build_failed_html]))
                remote_model_viewer = gr.HTML(label="模型结果",
                                              show_label=True,
                                              elem_id="model_viewer_container",
                                              visible=False)
        with gr.Row():
            with gr.Column():
                gr.HTML("<p>样例视频</p>", elem_classes="section_title")
                example_videos = gr.Dataset(label="",
                                            samples=list(map(lambda x: [x["cover"]], samples)),
                                            components=[gr.Image(visible=False)],
                                            elem_id="example_videos",
                                            container=False)
            with gr.Column():
                gr.HTML("<p>模型记录<span style='font-size:11px; color: #9ca3afcc; margin-left:6px;'>保留最近5个记录</span></p>", elem_classes="section_title")
                temp_btn = gr.Button(elem_id="temp_btn", visible=False)
                projects_html = gr.HTML(elem_id="projects_container")

        # upload steps:
        # fn 1. disable upload button, reset model_state_container, remote_model_viewer
        # fn 2. create project, return ak sk sts as json to temp text
        # fn 3. js upload video, on completion, set temp text
        # fn 4. save source, build project, reload projects section and select the first one.

        upload_helper_btn.click(upload_btn_on_click,
                                outputs=[source_video, model_state_container, remote_model_viewer])\
            .then(prepare_for_upload,
                  inputs=[jwt_token_txt, share_checkbox],
                  outputs=upload_helper_txt) \
            .then(fn=None,
                  inputs=upload_helper_txt,
                  outputs=[],
                  _js=upload_js)

        upload_completion_btn.click(upload_completion_btn_click, inputs=[jwt_token_txt, upload_helper_txt], outputs=[projects_html])\
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
                              """)\
            .then(fn=None, _js="""
                () => {
                    const example_videos = document.querySelector('#example_videos')
                    example_videos.style.pointerEvents = 'all'
                    example_videos.style.opacity = 1
                }
            """)
        update_email_btn.click(update_email_btn_click, inputs=[usr_email_text, jwt_token_txt], _js="() => [document.querySelector('#user_email textarea').value, document.querySelector('#jwt_token textarea').value]")
        temp_btn.click(temp_btn_on_click,
                       inputs=temp_btn,
                       outputs=[source_video, model_state_container, remote_model_viewer],
                       _js="() => document.querySelector('.project_vid_container.selected').getAttribute('data-model-url') ")\
            .then(fn=None,
                  _js="""
                        () => {
                            const source_video = document.querySelector("#video_input video")
                            if(source_video) {
                                source_video.src = document.querySelector('#temp_btn').textContent
                                source_video.play()
                            }
                            const glb_url = document.querySelector(".project_vid_container.selected").getAttribute("data-glb-url")
                            const download_btn = document.querySelector("#download_link")
                            download_btn?.setAttribute("href", glb_url) 
                        }
                  """)
    with gr.Tab("多图生成 (敬请期待)"):
        gr.Markdown("## <center>Coming soon!</center>")
    with gr.Tab("单图生成 (敬请期待)"):
        gr.Markdown("## <center>Coming soon!</center>")
    with gr.Tab("文本生成 (敬请期待)"):
        gr.Markdown("## <center>Coming soon!</center>")
    with gr.Column():
        gr.HTML("<h2 style='text-align:center; margin-top: 20px;'>模型案例</h2>")
        featured_projects_html = gr.HTML(elem_id="featured_projects_container")
    demo.load(fn=gr_on_load, inputs=uuid_txt, outputs=[jwt_token_txt, usr_email_text, projects_html, featured_projects_html], _js=app_js)\
        .then(fn=None,
              _js="""
                () => {
                    //select the most recent project if any.
                    const first_project_vid = document.querySelector('.project_vid_container')
                    if(first_project_vid) {
                        first_project_vid.click()
                    } 
                }
            """)

demo.launch()
