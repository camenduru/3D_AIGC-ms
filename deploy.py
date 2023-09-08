import os
import re


# function to open style.css file and replace any 'ggmotest/gg_xr_test' string with 'Damo_XR_Lab/3D_AIGC'
def update_path(file):
    print("Updating " + file)
    f = open(file, "r")
    lines = f.readlines()
    f.close()
    for i in range(len(lines)):
        if re.search('ggmotest/gg_xr_test', lines[i]):
            lines[i] = lines[i].replace('ggmotest/gg_xr_test', 'Damo_XR_Lab/3D_AIGC')
    f = open(file, "w")
    f.writelines(lines)
    f.close()

update_path('style.css')
update_path('htmls/video_upload_steps.html')
