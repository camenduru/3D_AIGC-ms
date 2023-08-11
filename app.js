async () => {
    let scriptEle = document.createElement("script")
    scriptEle.setAttribute("src", "https://gosspublic.alicdn.com/aliyun-oss-sdk-6.17.0.min.js");
    scriptEle.setAttribute("type", "text/javascript");
    scriptEle.setAttribute("async", "async");
    document.body.appendChild(scriptEle);

    const example_videos = document.getElementById("example_videos")

    const model_state_container = document.getElementById("model_state_container")
    const model_build_failed_container = document.getElementById("model_build_failed_container")
    const model_building_container = document.getElementById("model_building_container")
    const model_placeholder = document.getElementById("model_placeholder")
    
    model_build_failed_container.style.display='none'
    model_building_container.style.display='none'
    model_placeholder.style.display='flex'

    const gallery_items = example_videos.querySelectorAll(".gallery-item")
    gallery_items?.forEach(item => {
        item.addEventListener("click", function(e) {
            console.log("video clicked")
            gallery_items.forEach(e => { e.classList.remove("selected") })
            document.querySelectorAll(".project_vid_container")?.forEach(it => { it.classList.remove("selected")})
            this.classList.add("selected")
        })
    })

    const source_video = document.getElementById("video_input")
    const node = document.createElement("div")
    node.innerHTML = "<p style='color: #ccc; margin-top: 8px;'>选择下方样例或者模型记录查看视频</p>"
    source_video.querySelector(".svelte-lk9eg8.unpadded_box").append(node.firstChild)

    const video_upload_steps_container = document.getElementById("video_upload_steps_container")
    const video_info_container = video_upload_steps_container.querySelector("#video_info_container")
    const video_upload_input = video_upload_steps_container.querySelector("#video_upload_input")
    const select_video_btn = video_upload_steps_container.querySelector("#select_video_btn")
    const clear_btn = video_upload_steps_container.querySelector("#clear_btn")

    const share_checkbox = video_upload_steps_container.querySelector("#share")
    const upload_build_btn = video_upload_steps_container.querySelector("#upload_build_btn")

    video_upload_input.addEventListener("change", function() {
        const file = this.files[0];
        const video_url = URL.createObjectURL(file);
        if(video_url) {
            video_info_container.style.display = "flex"
            video_info_container.querySelector("#video_name").textContent = file.name
            video_info_container.querySelector("#video_size").textContent = (file.size / 1024 / 1024).toFixed(2) + "MB"

            clear_btn.style.display = "flex"
            select_video_btn.style.display = "none"

            upload_build_btn.disabled = false
        } else {
            clear_btn.style.display = "none"
            select_video_btn.style.display = "block"

            video_info_container.style.display = "none"
            upload_build_btn.disabled = true
        }
    })

    clear_btn.addEventListener("click", function() {

         video_info_container.style.display = "none"
         clear_btn.style.display = "none"
         select_video_btn.style.display = "block"
         upload_build_btn.disabled = true

         video_upload_input.value = ""
     })

     share_checkbox.addEventListener("change", function() {
        const gr_checkbox = document.querySelector("#gr_share_checkbox input")
        gr_checkbox.click()
     })

    upload_build_btn.addEventListener("click", function(e) {
        model_build_failed_container.style.display='none'
        model_building_container.style.display='none'
        model_placeholder.style.display='flex'

        const upload_helper_btn = document.getElementById("upload_helper_btn")
        upload_helper_btn.click()
    })

    globalThis.project_video_on_click = (e) => {
        console.log("project video clicked")
        var model_url = e.getAttribute("data-model-url")
        var status = e.getAttribute("data-status")
        console.log("model url", model_url)

        gallery_items?.forEach(it => { it.classList.remove("selected") })
        document.querySelectorAll(".project_vid_container")?.forEach(it => { it.classList.remove("selected")})
        e.classList.add("selected")

        const model_viewer_container = document.querySelector("#model_viewer_container")
        const model_viewer_container_child = model_viewer_container.querySelector("div.prose.svelte-1ybaih5")
        
        const model_state_container_child = model_state_container.querySelector("div.prose.svelte-1ybaih5")

        model_build_failed_container.style.display='none'
        model_building_container.style.display='none'
        model_placeholder.style.display='none'

        if (status == "VIEWABLE" && model_url) {
            console.log("display model")
            // model_state_container.classList.add("hidden")
            // model_viewer_container.classList.remove("hidden")

            // model_viewer_container_child.classList.remove("hide")
            // var model_iframe_wrapper = document.querySelector("#model_viewer_container.prose")
//            model_viewer_container_child.innerHTML = "<iframe class='model_container' src ='" + model_url + "'> </iframe>"
        } else {
            console.log("display other status")
            // model_viewer_container.classList.add("hidden")
            // model_state_container.classList.remove("hidden")

            // model_state_container_child.classList.remove("hide")
            
            if (status == "MAKING_FAILED") {
                model_build_failed_container.style.display='flex'
            } else if (status == "MAKING") {
                model_building_container.style.display='flex'
            } else {
                model_placeholder.style.display='flex'
            }
        }

        const temp_btn = document.querySelector("#temp_btn")
        temp_btn.textContent = e.querySelector("video").src
        temp_btn.click()
    }


    //guide video display
    window.document.onkeydown = function(e) {
        console.log(e)
        if (e.key == "Escape") {
            videoClose()
        }
      }
      
    document.querySelector("#view_guide_btn").addEventListener('click', function() {
        var lightBoxVideo = document.getElementById("guide_video");
        window.scrollTo(0, 0);
        document.getElementById('light').style.display = 'block';
        document.getElementById('fade').style.display = 'block';
        lightBoxVideo.play();
      })
      
    document.querySelector("#fade").addEventListener('click', videoClose)
    
    function videoClose() {
        var lightBoxVideo = document.getElementById("guide_video");
        document.getElementById('light').style.display = 'none';
        document.getElementById('fade').style.display = 'none';
        lightBoxVideo.pause();
      }
}