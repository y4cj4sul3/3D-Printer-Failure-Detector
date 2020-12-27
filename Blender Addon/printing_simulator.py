import bpy
import math
from os import path
import numpy as np
from mathutils import Matrix


class SetUpScene(bpy.types.Operator):
    """Set up scene"""
    bl_idname = "threedpfd.setup_scene"
    bl_label = "Setup Scene"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(maxlen=255)

    def execute(self, context):
        if path.exists(self.filepath):
            with open(self.filepath, 'rb') as fp:
                camPos = np.load(fp, allow_pickle=True)
                bpy.data.objects['Camera'].matrix_world = Matrix(camPos)
        else:
            print('Config not found: ' + self.filepath)
            bpy.data.objects['Camera'].location = (0.25, -.02, 0.12)
            bpy.data.objects['Camera'].rotation_euler = (math.radians(80), 0, math.radians(45))

        return {'FINISHED'}


class SliceSimulation(bpy.types.Operator):
    """Simulate slicing"""
    bl_idname = "threedpfd.slice_simulation"
    bl_label = "Simulation"
    bl_options = {'REGISTER', 'UNDO'}

    frame_duration: bpy.props.IntProperty(default=100)

    def execute(self, context):
        target = context.active_object
        print(target.name)

        # resize
        target.scale *= 0.001

        # turn Gcode into volumn (the operation take selected objects and active object)
        bpy.ops.object.convert(target='CURVE')
        target.data.bevel_depth = 0.175

        # simulate slice
        target.modifiers.new(name='Build', type='BUILD')
        target.modifiers["Build"].frame_duration = self.frame_duration
        context.scene.frame_end = self.frame_duration

        return {'FINISHED'}


class RenderPrinting(bpy.types.Operator):
    """Simulate slicing"""
    bl_idname = "threedpfd.render_printing"
    bl_label = "Render"

    frame_duration: bpy.props.IntProperty(default=100)
    filepath: bpy.props.StringProperty(maxlen=255)

    def execute(self, context):
        timestamp = []
        progress = []
        position = []
        # load progress
        with open(path.join(self.filepath, 'progress.txt'), 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                data = line.split(', ')

                timestamp.append(float(data[0]))
                progress.append(float(data[1]))
                position.append(
                    [float(data[2][1:]), float(data[3]), float(data[4][:-2])])
            # print(timestamp)
            # print(progress)
            # print(position)

        # TODO: loop each progress and find cooresponding frame by printhead position

        # # for progress in range(self.frame_duration):
        # progress = 10000
        # # set progress
        # context.scene.frame_set(progress)

        # # take picture
        # # TODO: modify path
        # context.scene.render.filepath = path.join(self.filepath, 'image.png')
        # bpy.ops.render.render(write_still=True)

        return {'FINISHED'}
