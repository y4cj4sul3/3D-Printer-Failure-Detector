import bpy
import math

def main(context):
    for ob in context.scene.objects:
        print(ob)

class SetUpScene(bpy.types.Operator):
    """Set up scene"""
    bl_idname = "threedpfd.setup_scene"
    bl_label = "Setup Scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        # TODO: viewpoint depends on machine
        # set viewpoint
        bpy.data.objects['Camera'].location = (0.2, 0, 0.2)
        bpy.data.objects['Camera'].rotation_euler = (math.radians(80), 0, math.radians(45))
        
        return {'FINISHED'}


class SliceSimulation(bpy.types.Operator):
    """Simulate slicing"""
    bl_idname = "threedpfd.slice_simulation"
    bl_label = "Simulation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        target = context.active_object
        
        # resize
        target.scale *= 0.001
        
        # turn Gcode into volumn
        bpy.ops.object.convert(target='CURVE')
        target.data.bevel_depth = 0.175
        
        # simulate slice
        target.modifiers.new(name='Build', type='BUILD')
        #target.modifiers['Build']
        # FIXME: reverse
        
        # set timeline
        context.scene.frame_set(50)
        
        # take picture
        # TODO: modify path
        context.scene.render.filepath = 'image.png'
        bpy.ops.render.render(write_still=True)
        
        return {'FINISHED'}
    
class ThreeDPFDPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "3DPFD"
    bl_idname = "SCENE_PT_3DPFD"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        
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


def register():
    bpy.utils.register_class(SetUpScene)
    bpy.utils.register_class(SliceSimulation)
    bpy.utils.register_class(ThreeDPFDPanel)


def unregister():
    bpy.utils.unregister_class(SetUpScene)
    bpy.utils.unregister_class(SliceSimulation)
    bpy.utils.unregister_class(ThreeDPFDPanel)


if __name__ == "__main__":
    register()
