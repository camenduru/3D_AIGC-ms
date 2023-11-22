() => {
    const source_video = document.querySelector("#video_input video")
    if (source_video) {
        source_video.src = document.querySelector('#temp_btn').textContent
        source_video.muted = true
        source_video.play()
    }
    const project_item = document.querySelector(".project_vid_container.selected")

    const glb_url = project_item.getAttribute("data-glb-url")
    const new_glb_url = document.querySelector("#download_helper_txt textarea").value
    // console.log("new glb url, ", new_glb_url)
    const download_btn = document.querySelector("#sd_download_link")
    if (new_glb_url) {
        download_btn?.setAttribute("href", new_glb_url)
    } else {
        download_btn?.setAttribute("href", glb_url)
    }
}