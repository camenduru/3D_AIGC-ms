() => {
    /**
     * functions definitions
     * */
    //convert parameters object to string
    const stringifyObject = obj => Object.keys(obj).map((k) => k + '=' + obj[k]).join('&');

    // function to get url parameter
    const getUrlParameterValue = (paramName, window) => {
        let sPageURL = decodeURIComponent(window.location.search.substring(1)),
            sURLVariables = sPageURL.split('&'),
            sParameterName,
            i;

        for (i = 0; i < sURLVariables.length; i++) {
            sParameterName = sURLVariables[i].split('=');

            if (sParameterName[0] === paramName) {
                return sParameterName[1] === undefined ? "" : sParameterName[1];
            }
        }
    };

    //function to send tracking events
    const sendEventTracking = (eventName, eventParams = {}) => {
        let q = window.aplus_queue || [];
        // append userId to eventParams
        if (!eventParams['user_id']) {
            eventParams['user_id'] = document.querySelector("#uuid textarea").value || ''
        }
        q.push({
            action: 'aplus.record',
            arguments: [
                eventName,//事件ID
                'CLK', //事件类型
                stringifyObject(eventParams), //参数
                'GET'
            ]
        });

        //使用addBehavior接口上报用户点击事件
        let bl = window.__bl || [];
        // console.log("bl", bl)
        bl.addBehavior({
            data:{
                name: eventName.replace("/ms_3d_obj.", ""),
                message: stringifyObject(eventParams)
            },
        })
    };

    /**
     * functions calling and actions
     * */
    //select the most recent project if any.
    const first_project_vid = document.querySelector('.project_vid_container')
    if (first_project_vid) {
        first_project_vid.click()
    }
    //show email popup link if needed.
    const saved_email = document.querySelector("#user_email textarea").value
    console.log("saved email:", saved_email)
    const notify_link = document.querySelector("#notify_link")
    if (saved_email) {
        notify_link.style.display = "none"
    } else {
        notify_link.style.display = "block"
    }

    const share_popup = document.querySelector("#share_popup")
    const link_input = share_popup.querySelector("#share_link")
    const copy_share_link_btn = document.querySelector("#copy_share_link")
    const share_popup_close_btn = document.querySelector("#share_popup_close_btn")
    const qrcode_img = document.querySelector("#qrcode")

    globalThis.shareModelClick = () => {
        console.log("share clicked")
        share_popup.style.display = "block"
        copy_share_link_btn.textContent = "复制链接"
        copy_share_link_btn.disabled = false

        const iframe = document.querySelector("#model_viewer_container iframe")
        link_input.value = iframe.src
        link_input.disabled = true

        qrcode_img.innerHTML = ""
        const qrc = new QRCode(qrcode_img, {
            text: link_input.value,
            width: 200,
            height: 200,
        });
        //send tracking event
        sendEventTracking('/ms_3d_obj.projects.click_share')
    }

    copy_share_link_btn.addEventListener("click", function(e) {
        navigator.clipboard.writeText(link_input.value).then(function() {
            console.log("已复制: ", link_input.value)
            copy_share_link_btn.textContent = "已复制！"
            copy_share_link_btn.disabled = true
        },function(err) {
            console.error('复制失败', err);
        })
    })

    share_popup_close_btn.onclick = function() {
        share_popup.style.display = "none";
    }

    globalThis.downloadLinkClick = () => {
        //track click download
        sendEventTracking('/ms_3d_obj.projects.click_download')
    }

    // 是否来源于邮件点击
    const from_email = getUrlParameterValue("from_email", window.parent)
    // 项目ID
    const project_id = getUrlParameterValue("project_id", window.parent)
    // 是否成功
    const is_success = getUrlParameterValue("is_success", window.parent)

    // 拿到aplus对象
    const q = (window.aplus_queue || (window.aplus_queue = []));
    console.log("aplus", q)
    const path = window.parent.location.pathname
    console.log("current path after domain:", path)

    const is_prod =  (path.indexOf('3D_AIGC') !== -1) //线上创空间名字为3D_AIGC
    // 添加PV任务
    q.push({
        // 设置spm信息
        'action': 'aplus.setPageSPM',
        // 设置站点, 页面：spma, spmb
        'arguments': ['3d_obj', is_prod ? 'home' : 'test_home']
    });
    q.push({
        'action': 'aplus.sendPV',
        'arguments': [{
            is_auto: false // 写死即可
        }, {
            // 自定义PV参数key-value键值对
            // 注意：key不能以aliyun、aplus开头，否则会被过滤掉
            // 'user_agent': navigator.userAgent
            // 是否来源于邮件点击
            from_email: from_email,
            // 项目ID
            project_id: project_id,
            // 是否成功
            is_success: is_success
        }]
    });

    // send event if click from email
    if (from_email === 'true') {
        console.log("open from email")
        sendEventTracking("/ms_3d_obj.other.open_from_email", {
            project_id: project_id,
            is_success: is_success
        })
    }

    //track click guide video
    const vid_guide_btn = document.querySelector('#view_guide_btn');
    vid_guide_btn.addEventListener('click', function() {
        sendEventTracking('/ms_3d_obj.onboarding.click_guide_video');
    });

    //track choose file input
    const choose_file_btn = document.querySelector('#select_video_btn');
    choose_file_btn.addEventListener('click', function() {
        sendEventTracking('/ms_3d_obj.upload_build.click_choose_file');
    });

    //track share to featured checkbox click
    const share_checkbox = document.querySelector("#share_check")
    share_checkbox.addEventListener('click', function() {
        sendEventTracking('/ms_3d_obj.upload_build.click_share_to_featured_check', {
            is_checked: share_checkbox.checked
        });
    });

    //track upload button click
    const upload_btn = document.querySelector('#upload_build_btn');
    upload_btn.addEventListener("click", function() {
        sendEventTracking('/ms_3d_obj.upload_build.click_upload');
    })

    //track featured video click
    const featured_videos = document.querySelectorAll(".featured_model_vid");
    featured_videos.forEach(function (item, index) {
        item.addEventListener("click", function () {
            sendEventTracking('/ms_3d_obj.featured.click_featured_3dmodel', { index: index + 1 });
        })
    })

    //track example video click
    const example_videos = document.querySelectorAll(".gallery-item")
    example_videos.forEach(function (item, index) {
        item.addEventListener("click", function () {
            sendEventTracking('/ms_3d_obj.demo.click_example_video', { index: index + 1 });
        })
    })

    //track projects
    const project_videos = document.querySelectorAll(".project_vid_container")
    project_videos.forEach(function (item, index) {
        item.addEventListener("click", function () {
            sendEventTracking('/ms_3d_obj.projects.click_project', { index: index + 1, project_id: item.getAttribute('project-id') });
        })
    })
    //track click view mesh button
    globalThis.model_iframe_on_load = (e) => {
        console.log("model iframe loaded")
    }

    window.onmessage = function (event){
        //convert event.data string to json object
        console.log("receive message data: ", event.data, event.origin)
        const evData = event.data
        if (evData.event !== "eventTracking") {
            return
        }
        //send tracking event
        switch (evData.type) {
            case "view_model":
                sendEventTracking('/ms_3d_obj.projects.click_view_model')
                break;
            case "view_mesh":
                sendEventTracking('/ms_3d_obj.projects.click_view_mesh')
                break;
            default:
                break;
        }
    }
}