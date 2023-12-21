() => {

    const path = window.location.href
    console.log("current path after domain:", path)
    const is_prod =  (path.indexOf('3D_AIGC') !== -1) //线上创空间名字为3D_AIGC
    /**
     * functions definitions
     * */
    //convert parameters object to string
    const stringifyObject = obj => Object.keys(obj).map((k) => k + '=' + obj[k]).join('&');

    // function to get url parameter
    // const getUrlParameterValue = (paramName, window) => {
    //     let sPageURL = decodeURIComponent(window.location.search.substring(1)),
    //         sURLVariables = sPageURL.split('&'),
    //         sParameterName,
    //         i;
    //
    //     for (i = 0; i < sURLVariables.length; i++) {
    //         sParameterName = sURLVariables[i].split('=');
    //
    //         if (sParameterName[0] === paramName) {
    //             return sParameterName[1] === undefined ? "" : sParameterName[1];
    //         }
    //     }
    // };

    //function to send tracking events
    const sendEventTracking = (eventName, eventParams = {}) => {
        let q = window.aplus_queue || [];
        // append userId to eventParams
        if (!eventParams['user_id']) {
            eventParams['user_id'] = document.querySelector("#uuid textarea").value
        }
        // console.log(eventParams)
        q.push({
            action: 'aplus.record',
            arguments: [
                eventName,//事件ID
                'CLK', //事件类型
                stringifyObject(eventParams), //参数
                'GET'
            ]
        });

        if (is_prod) {
            //ARMS 平台事件埋点
            let b = window.__bl || [];
            b.event({
                key: eventName, //事件key，必填
                // success: false, //事件成功与否，非必填，默认true
                // time: 100, //事件耗时ms，非必填
                c1: 'CLK', //自定义字段c1，非必填
                c2: stringifyObject(eventParams), //自定义字段c2，非必填
                // c3: 'xxx', //自定义字段c3，非必填
            });
        }
    };

    /**
     * functions calling and actions
     * */

    // 是否来源于邮件点击
    // const param_from_email = getUrlParameterValue("from_email", window.parent)
    // 项目ID
    // const param_project_id = getUrlParameterValue("project_id", window.parent)
    // 是否成功
    // const param_is_success = getUrlParameterValue("is_success", window.parent)

    // 拿到aplus对象
    const q = (window.aplus_queue || (window.aplus_queue = []));
    console.log("aplus", q)

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
            // from_email: param_from_email,
            // 项目ID
            // project_id: param_project_id,
            // 是否成功
            // is_success: param_is_success
        }]
    });

    // send event if click from email
    // if (param_from_email === 'true') {
    //     console.log("open from email")
    //     sendEventTracking("/ms_3d_obj.other.open_from_email", {
    //         project_id: param_project_id,
    //         is_success: param_is_success
    //     })
    // }

    //select the most recent project if any.
    const first_project_vid = document.querySelector('.project_vid_container')
    if (first_project_vid) {
        first_project_vid.click()
    }
    //show email popup link if needed.
    const saved_email = document.querySelector("#user_email textarea").value
    // console.log("saved email:", saved_email)
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

    function open_share_modal(source) {
        share_popup.style.display = "block"
        copy_share_link_btn.textContent = "复制链接"
        copy_share_link_btn.disabled = false

        link_input.value = source
        link_input.disabled = true

        qrcode_img.innerHTML = ""
        new QRCode(qrcode_img, { // eslint-disable-line
            text: link_input.value,
            width: 200,
            height: 200,
        });
    }

    globalThis.shareSDModelClick = (source) => {
        console.log("share clicked")
        open_share_modal(source)
        //send tracking event
        sendEventTracking('/ms_3d_obj.projects.click_share')
    }

    copy_share_link_btn.addEventListener("click", function() {
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

    globalThis.downloadSDModelLinkClick = () => {
        //track click download
        sendEventTracking('/ms_3d_obj.projects.click_download')
    }

    globalThis.shareHDModelClick = (source) => {
        open_share_modal(source)
        sendEventTracking('/ms_3d_obj.projects.click_share')
    }

    globalThis.downloadHDModelLinkClick = () => {
        sendEventTracking('/ms_3d_obj.projects.click_download')
    }

    globalThis.tab_item_click = function (tab, index1) {
        const parent = tab.parentElement
        const children = Array.from(parent.children)
        children.forEach((child) => child.classList.remove("active"))
        tab.classList.add("active")

        document.querySelectorAll(".tab-content").forEach(function (content, index2) {
            if (index1 === index2) {
                content.style.display = "block"
            } else {
                content.style.display = "none"
            }
        })
        const iframe = document.querySelector("#hd_model_viewer")
        if (index1 === 0 && !iframe.src) {
            trigger_hd_project_reload()
        }

        const project_item = document.querySelector(".project_vid_container.selected")
        const project_id = project_item.getAttribute('project-id')
        if (index1 === 0) {
            sendEventTracking("/ms_3d_obj.projects.click_hd_model_result", {
                project_id: project_id,
            })
        } else if (index1 === 1) {
            sendEventTracking("/ms_3d_obj.projects.click_fast_model_result", {
                project_id: project_id,
            })
        }
    }

    const tabs = document.querySelectorAll(".tab-nav")
    tabs.forEach(function (item, index) {
        item.addEventListener("click", function (e) {
            const tab = e.target
            sendEventTracking("/ms_3d_obj.tab.click_tab", {
                tab: tab.textContent,
                index: index
            })
        })
    })

    function trigger_hd_project_reload() {
        console.log("trigger hd project reload")
        const hd_helper_button = document.querySelector("#hd_helper_button")
        hd_helper_button.click()
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

    // track search
    const search_btn = document.querySelector('#search_btn');
    search_btn.addEventListener('click', function() {
        const search_type = document.querySelector('#search_type_radio .wrap label.selected span').textContent
        const search_txt = document.querySelector('#search_input_txt textarea').value.trim()
        console.log("search type: ", search_type, "search txt: ", search_txt)
        sendEventTracking('/ms_3d_obj.click_search', { type: search_type, search_query: search_txt});
    });

    //track click view mesh button
    globalThis.model_iframe_on_load = () => {
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