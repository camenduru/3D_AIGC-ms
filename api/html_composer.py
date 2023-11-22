from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup

model3d_actions_html = Path("htmls/model3d_actions.html").read_text()
project_item_html = Path("htmls/project_item.html").read_text()
model_video_item = Path("htmls/model_video_item.html").read_text()


def model_preview_url(url, title):
    if not url:
        return ""
    return f"https://market.m.taobao.com/app/xr-paas/xr-paas-portal/index.html#/h5-modelviewer?modelUrl={quote(url)}&modelName={quote(title)}&bizUsage=inverse_rendering"


def single_model_viewer_iframe(url, glb_url, title, show_actions: bool):
    iframe = f"""<iframe class='model_container' src ='{model_preview_url(url, title)}'></iframe>"""
    iframe += model3d_actions_html if show_actions else ""

    soup = BeautifulSoup(iframe, 'html.parser')
    download_action = soup.select_one("#download_link")
    if download_action:
        download_action["href"] = glb_url
    share_action = soup.select_one("#share_action")
    if share_action:
        share_action["onclick"] = f"shareSDModelClick('{model_preview_url(url, title)}')"

    return str(soup)


# project list 格式：参看api_manager.parse_project_list返回值
def project_list_html(project_list):
    if not project_list:
        return "<div style='text-align: center;'>暂无数据</div>"

    def get_model_url(proj):
        # print("proj", proj)
        try:
            preview_url = proj.preview_url
            if not preview_url:
                return None
            else:
                soup = BeautifulSoup(model_video_item, 'html.parser')
                model_video = soup.select_one(".model_video_item")
                model_video["style"] = f"background-image: url('{proj.cover_url}');"
                model_video["src"] = preview_url
                model_video["onclick"] = f"window.open('{model_preview_url(proj.model_url, proj.title)}', '_blank')"

                download_action = soup.select_one("#download_link")
                download_action["href"] = proj.glb_url

                share_action = soup.select_one("#share_action")
                share_action["onclick"] = f"shareSDModelClick('{model_preview_url(proj.model_url, proj.title)}')"
                return str(soup)

        except IndexError:
            return None

    proj_model_htmls = [item for item in list(map(get_model_url, project_list)) if item is not None]
    css_classes = "featured_model_list_container center_for_one" if len(
        proj_model_htmls) == 1 else "featured_model_list_container"
    return f"<div style='display: block;'><div class='{css_classes}'>" + "".join(proj_model_htmls) + "</div></div>"


def project_video_constructor(project_id, hd_project_id, fast_project_id, video_url, video_cover_url, status, model_url,
                              glb_url):
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

    soup = BeautifulSoup(project_item_html, 'html.parser')
    project_vid_container = soup.select_one(".project_vid_container")
    project_vid_container["data-project-id"] = project_id
    project_vid_container["data-hd-project-id"] = hd_project_id
    project_vid_container["data-fast-project-id"] = fast_project_id
    project_vid_container["data-model-url"] = actual_model_url
    project_vid_container["data-glb-url"] = actual_glb_url
    project_vid_container["data-status"] = status

    project_status_overlay = soup.select_one(".project_status_overlay")
    project_status_overlay["style"] = display_status

    project_status_p = soup.select_one(".project_status_overlay p")
    project_status_p["style"] += f"color: {color};"
    project_status_p.string = actual

    project_vid = soup.select_one(".project_vid")
    project_vid["video-src"] = video_url
    project_vid["src"] = video_cover_url
    return str(soup)
