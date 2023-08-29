(params) => {
    console.log("project sts:", params)

    const video_upload_steps_container = document.getElementById("video_upload_steps_container")
    // const video_info_container = video_upload_steps_container.querySelector("#video_info_container")
    const video_upload_input = video_upload_steps_container.querySelector("#video_upload_input")
    // const select_video_btn = video_upload_steps_container.querySelector("#select_video_btn")
    const upload_clear_btn = video_upload_steps_container.querySelector("#clear_btn")
    const upload_build_btn = video_upload_steps_container.querySelector("#upload_build_btn")

    const upload_completion_btn = document.querySelector("#upload_completion_btn")
    const upload_helper_txt = document.querySelector("#upload_helper_txt")
    const user_email_txt = document.querySelector("#user_email")

    const completion_popup = document.querySelector("#completion_popup")
    const progress_bar = document.querySelector("#progress_bar")

    upload_build_btn.disabled = true
    upload_clear_btn.style.opacity = 0

    const file = video_upload_input.files[0]
    const file_name = encodeURIComponent(file.name)
    var sts_json = null;
    try {
        sts_json = JSON.parse(params);
        console.log("sts result:", sts_json)
    } catch (e) {
        return alert('上传失败: ' + e.message);
    }
    const client = new OSS({
        accessKeyId: sts_json.ak,
        accessKeySecret: sts_json.sk,
        stsToken: sts_json.sts,
        region: sts_json.region,
        bucket: sts_json.bucket
    });

    const options = {
        progress: (p, cpt, res) => {
            console.log("上传进度", p)
            upload_build_btn.textContent = `上传中...(${(p * 100).toFixed(1)}%)`
            progress_bar.style.width = `${p*100}%`
        },
        headers: {
            "name": file_name,
            "key": sts_json.key + file_name,
            "success_action_status": "200",
            "expire": sts_json.expire
        }
    }
    console.log("upload", file_name, sts_json.key + file_name)
    var intervalHandle = null
    client.multipartUpload(sts_json.key + file_name, file, options)
        .then(function (result) {
            console.log("上传结果", result)
            if (result.res.statusCode == 200) {
                upload_clear_btn.click()
                upload_clear_btn.style.opacity = 1
                progress_bar.style.width = 0
                result["success"] = true
                upload_helper_txt.querySelector("textarea").value = JSON.stringify(result)
                upload_build_btn.textContent = "上传并生成模型"
                upload_completion_btn.click()

                //show email notification popup
                completion_popup.style.display = "block"
                const error_msg = document.querySelector("#error")
                error_msg.style.opacity = 0

                const saved_email = user_email_txt.querySelector("textarea").value
                const submit_btn = document.querySelector("#submit_btn")
                if (saved_email) {
                    document.querySelector("#email").value = saved_email
                    document.querySelector("#email_hint").textContent = "您已留下邮箱地址，模型构建结果会邮件通知您:"

                    submit_btn.style.opacity = 0.6
                    submit_btn.disabled = false

                    var secs = 5
                    const skip_txt = document.querySelector("#skip")
                    skip_txt.style.display = "block"
                    skip_txt.textContent = "5秒后关闭"
                    intervalHandle = setInterval(() => {
                        secs = secs - 1
                        document.querySelector("#skip").textContent = `${secs}秒后关闭`
                        if (secs == 0) {
                            clearInterval(intervalHandle)
                            completion_popup.style.display = "none"
                        }
                    }, 1000);
                } 
            }
        }).catch(function (err) {
            console.log("上传失败:", err)
            alert("上传失败，请稍后重试。")
            upload_clear_btn.style.opacity = 1
            progress_bar.style.width = 0
            upload_helper_txt.querySelector("textarea").value = `{"success": false, "error": ${err}}`
        })

        document.querySelector("#email").addEventListener("input", function(e) {
            clearInterval(intervalHandle)
            const saved_email = user_email_txt.querySelector("textarea").value
            const skip_txt = document.querySelector("#skip")
            skip_txt.textContent = "不想留邮箱，1小时后回来查看"
            if (saved_email) {
                skip_txt.style.display = "none"
            } else {
                skip_txt.style.display = "block"
            }
        })
}