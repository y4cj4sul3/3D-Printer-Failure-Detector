import bpy

from . import printing_simulator as ps
from . import user_interface as ui


bl_info = {
    "name": "3D Printer Failure Detection Simulator",
    "author": "y4cj4sul3",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D View > 3DPFD Simulator",
    "description": "Simulate printing progress",
    "warning": "",
    "doc_url": "",
    "category": "Development",
}


classes = (
    ps.SetUpScene,
    ps.SliceSimulation,
    ps.RenderPrinting,
    ui.GcodeImporter,
    ui.ThreeDPFDPanel,
    ui.AllInOne
)


def register():
    import importlib
    importlib.reload(ps)
    importlib.reload(ui)

    for c in classes:
        bpy.utils.register_class(c)


def unregister():

    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
