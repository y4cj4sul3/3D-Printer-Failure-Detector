import bpy
import math


class SetUpScene(bpy.types.Operator):
    """Set up scene"""
    bl_idname = "threedpfd.setup_scene"
    bl_label = "Setup Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        # TODO: viewpoint depends on machine
        # set viewpoint
        bpy.data.objects['Camera'].location = (0.25, -.02, 0.2)
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

        return {'FINISHED'}


class RenderPrinting(bpy.types.Operator):
    """Simulate slicing"""
    bl_idname = "threedpfd.render_printing"
    bl_label = "Render"

    frame_duration: bpy.props.IntProperty(default=100)

    def execute(self, context):
        for progress in range(self.frame_duration):
            # set progress
            # TODO: set build plate height
            context.scene.frame_set(progress)

            # take picture
            # TODO: modify path
            context.scene.render.filepath = 'image.png'
            bpy.ops.render.render(write_still=True)
