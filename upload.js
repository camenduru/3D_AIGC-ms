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

    upload_build_btn.disabled = true

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
            // uploading_container.style.display = "block"

            // uploading_container.querySelector("p").textContent = `上传中...(${(p * 100).toFixed(1)}%)`
            upload_build_btn.textContent = `上传中...(${(p * 100).toFixed(1)}%)`
        },
        headers: {
            "name": file_name,
            "key": sts_json.key + file_name,
            "success_action_status": "200",
            "expire": sts_json.expire
        }
    }
    console.log("upload", file_name, sts_json.key + file_name)
    client.multipartUpload(sts_json.key + file_name, file, options)
        .then(function (result) {
            console.log("上传结果", result)
            if (result.res.statusCode == 200) {
                // uploading_container.style.display = "none"
                upload_clear_btn.click()
                result["success"] = true
                upload_helper_txt.querySelector("textarea").value = JSON.stringify(result)
                upload_build_btn.textContent = "上传并生成模型"
                upload_completion_btn.click()
            }
        }).catch(function (err) {
            console.log("上传失败:", err)
            alert("上传失败，请稍后重试。")
            upload_helper_txt.querySelector("textarea").value = `{"success": false, "error": ${err}}`
        })
}