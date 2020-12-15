import bpy

from . import gcode_parser as gp
# from . import printing_simulator as ps

from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy.types import Operator, PropertyGroup, Panel
from bpy_extras.io_utils import ImportHelper


class ThreeDPFDPanel(Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "3DPFD"
    bl_idname = "SCENE_PT_3DPFD"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        # Import Gcode
        layout.label(text="Import Gcode:")
        row = layout.column()
        row.scale_y = 2.0
        row.operator("threedpfd.gcode_import")

        # Set up scene
        layout.label(text="Setup Scene:")
        row = layout.row()
        row.scale_y = 2.0
        row.operator("threedpfd.setup_scene")

        # Slice simulation
        layout.label(text="Simulate:")
        row = layout.row()
        row.scale_y = 2.0
        row.operator("threedpfd.slice_simulation")

        # All in one
        layout.label(text="All in One:")
        row = layout.row()
        row.scale_y = 2.0
        row.operator("threedpfd.all_in_one")


def gcodeImporter(filepath):
    print('read gcode file', filepath)

    import time
    then = time.time()

    # load and parse file
    parser = gp.GcodeParser()
    model = parser.parseFile(filepath)
    # model.subdivide(?)
    # convert to mesh data
    model.classifySegments()
    time_height = model.draw()

    now = time.time()
    print('then', then)
    print("importing Gcode took", now-then)

    return time_height


class GcodeImporter(Operator, ImportHelper):
    """Import Gcode"""
    bl_idname = "threedpfd.gcode_import"
    bl_label = "Import Gcode"

    filename_ext = ".gcode"

    filter_glob: StringProperty(
        default="*.gcode",
        options={'HIDDEN'},
        maxlen=255
    )

    def execute(self, context):
        gcodeImporter(self.filepath)

        return {'FINISHED'}


class AllInOne(Operator):
    """All Operation in Once"""
    bl_idname = "threedpfd.all_in_one"
    bl_label = "All In One"

    filepath: StringProperty(
        default="*.gcode",
        maxlen=255
    )

    def execute(self, context):
        # import gcode
        self.filepath = 'path/to/file.gcode'
        print(self.filepath)
        time_height = gcodeImporter(self.filepath)
        print("G-code imported")

        # setup scene
        bpy.ops.threedpfd.setup_scene()
        print("Setup Scene")

        # deselect all object
        for obj in context.selected_objects:
            obj.select_set(False)
        # select only the target object
        target = bpy.data.objects['Gcode']
        target.select_set(True)
        context.view_layer.objects.active = target

        # TODO: this should be in simulator
        # set animation
        for frame, height in time_height:
            target.location[2] = 0.2 - height / 1000
            target.keyframe_insert(data_path="location", frame=frame, index=2)

        # simulate
        bpy.ops.threedpfd.slice_simulation(frame_duration=time_height[-1][0])
        print("Simulate")

        # render
        # bpy.ops.threedpfd.render_printing(frame_duration=100)

        return {'FINISHED'}