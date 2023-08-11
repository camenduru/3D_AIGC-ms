import math
import os.path

from pygltflib import GLTF2, BufferFormat
from pygltflib.utils import glb2gltf
from transformations import transformations


def transform_model(model_name):
    glb_path = f"resource/{model_name}.glb"
    gltf_path = f"resource/{model_name}.gltf"
    bin_path = f"resource/{model_name}.bin"

    if os.path.exists(gltf_path):
        success = True
    else:
        success = glb2gltf(glb_path)
    if success:
        gltf = GLTF2().load(gltf_path)
        gltf.extensionsUsed = ["KHR_materials_unlit"]
        for mat in gltf.materials:
            mat.extensions["KHR_materials_unlit"] = {}
        node_index = gltf.scenes[gltf.scene].nodes[0]
        root = gltf.nodes[node_index]
        quat = transformations.quaternion_from_euler(-math.pi/2, math.pi/2, 0, axes="sxyz")  # output is w, x, y, z
        root.rotation = (quat[1], quat[2], quat[3], quat[0])  # gltf quaternion is x, y, z, w
        gltf.convert_buffers(BufferFormat.DATAURI)
        gltf.save(gltf_path)
        if os.path.exists(bin_path):
            os.remove(bin_path)
        print("gltf saved")
