() => {
    const hd_result = document.querySelector("#hd_model_result")
    if (!hd_result) {
        return
    }
    const building_div = hd_result.querySelector("#hd_model_building")
    const failed_div = hd_result.querySelector("#hd_model_failed")
    const viewer_div = hd_result.querySelector("#hd_model_viewer")
    const hd_model_actions_div = hd_result.querySelector("#hd_model_actions")
    // const model_loading_div = hd_result.querySelector("#hd_model_loading")
    building_div.style.display = "none";
    failed_div.style.display = "none";
    viewer_div.style.display = "none";
    hd_model_actions_div.style.display = "none";
    // model_loading_div.style.display = "none";

    const result = document.querySelector("#hd_help_text textarea").value
    if (!result) {
        building_div.style.display = "flex";
        return
    }
    const obj = JSON.parse(result)
    console.log("hd result data", obj)
    switch (obj.status) {
        case "MAKING_FAILED":
            failed_div.style.display = "block"
            break;
        case "VIEWABLE":
            // model_loading_div.style.display = "block";
            hd_model_actions_div.style.display = "flex";
            viewer_div.style.display = "block"
            const url = `https://market.m.taobao.com/app/xr-paas/xr-paas-portal/index.html#/h5-modelviewer?modelUrl=${encodeURIComponent(obj.model_url)}&modelName=${encodeURIComponent(obj.name)}&bizUsage=inverse_rendering`
            viewer_div.src = url
            viewer_div.onload = function () {
                // model_loading_div.style.display = "none";
            };
            break;
        default:
            building_div.style.display = "flex"
            break;
    }

    const hd_download_btn = document.querySelector("#hd_download_link")
    hd_download_btn?.setAttribute("href", obj.glb_url)
}