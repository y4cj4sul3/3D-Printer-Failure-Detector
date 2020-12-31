import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy.types import Operator, PropertyGroup, Panel
from bpy_extras.io_utils import ImportHelper

from os import path
import numpy as np

from . import gcode_parser as gp
# from . import printing_simulator as ps


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
    model.subdivide(1)
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


def allInOne(context, filepath):
    # clear scene (delete default cube)
    bpy.ops.object.delete(use_global=False)

    # import gcode
    gcode_path = path.join(filepath, 'path.gcode')
    print(gcode_path)
    verts, edges, time_height = gcodeImporter(gcode_path)
    print("G-code imported")

    # setup scene
    config_path = path.join('/'.join(filepath.split('/')[:-1]), 'calibration/camera_pose.npy')
    bpy.ops.threedpfd.setup_scene(filepath=config_path)
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
        target.location[2] = - height / 1000
        target.keyframe_insert(data_path="location", frame=frame, index=2)

    # simulate
    frame_duration = time_height[-1][0]
    bpy.ops.threedpfd.slice_simulation(frame_duration=frame_duration)
    print("Simulate")

    # render
    render_printing(context, frame_duration, filepath, verts, edges)
    # bpy.ops.threedpfd.render_printing(frame_duration=frame_duration, filepath=filepath)


class AllInOne(Operator):
    """All Operation in Once"""
    bl_idname = "threedpfd.all_in_one"
    bl_label = "All In One"

    filepath: StringProperty(
        default="",
        maxlen=255
    )

    def execute(self, context):
        if path.exists(self.filepath):
            allInOne(context, self.filepath)
        else:
            print('file not exist')

        return {'FINISHED'}


def render_printing(context, frame_duration, filepath, verts, edges, layer_th=0.03, subdivide_th=1):
    # rendering settings
    context.scene.render.resolution_x = 800
    context.scene.render.resolution_y = 600
    context.scene.render.film_transparent = True
    # TODO: set focal length

    timestamp = []
    # progress = []
    position = []
    # load progress
    with open(path.join(filepath, 'new_progress.txt'), 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            data = line.split(', ')
            if len(data) == 5:
                pos = [float(data[2][1:]), float(data[3]), float(data[4][:-2])]
                if not np.isnan(pos).any():
                    timestamp.append(float(data[0]))
                    # progress.append(float(data[1]))
                    position.append(pos)

        # print(timestamp)
        # print(progress)
        # print(position)
    position = np.array(position)

    # TODO: loop each progress and find cooresponding frame by printhead position
    verts = np.array(verts)
    edges.reverse()
    edges = np.array(edges)

    cur_pos = 0
    cur_vtx = 0
    cur_edge = 0

    num_pos = len(position)
    num_vtx = len(verts)

    # match the first layer
    # since the recorded progress may start from the middle
    # minimum layer of height of ultimaker is 0.06 mm
    while cur_vtx < num_vtx and position[cur_pos, 2] - verts[cur_vtx, 2] > layer_th:
        cur_vtx += 1

    if cur_vtx == num_vtx:
        print('No matching layer height')
        return

    # goal: find closest simulated frame to the input progress
    num_matches = 0
    num_valid_matches = 0
    while cur_pos < num_pos and cur_vtx < num_vtx:
        layer_height = position[cur_pos, 2]
        print('Layer Height:', layer_height)
        # find the next layer index
        nl_pos = cur_pos
        while nl_pos < num_pos and position[nl_pos, 2] - layer_height < layer_th:
            nl_pos += 1

        nl_vtx = cur_vtx
        while nl_vtx < num_vtx and verts[nl_vtx, 2] - layer_height < layer_th:
            nl_vtx += 1

        print(nl_pos - cur_pos, nl_vtx - cur_vtx)

        matches = []
        for i in range(cur_pos, nl_pos):
            pos = position[i]
            # print(cur_pos, pos)
            # find closest vertex
            closest_vtx = np.argmin(np.linalg.norm(verts[cur_vtx:nl_vtx] - pos, axis=1)) + cur_vtx
            distance = np.linalg.norm(verts[closest_vtx] - pos)
            # print(closest_vtx, verts[closest_vtx], distance)

            # skip progress that distance excessed threshold (subdivide threshold)
            if distance < subdivide_th:
                matches.append([i, closest_vtx])
            # else:
            #     print('not match')

        print('Matches: {}/{}'.format(len(matches), nl_pos - cur_pos))
        num_matches += len(matches)

        if len(matches) > 0:
            # ascending check
            valid_matches = [matches[0]]    # assume first match is valid
            for i in range(1, len(matches)):
                if matches[i][1] > matches[i-1][1]:
                    valid_matches.append(matches[i])

            print('Valid Matches: {}/{}'.format(len(valid_matches), len(matches)))
            num_valid_matches += len(valid_matches)

            # find edge index, which is the frame index
            # while edges[cur_edge][1] < cur_vtx:
            #     cur_edge += 1
            # print(cur_edge, edges[cur_edge])

            # for progress in range(0, frame_duration, frame_duration//100):
            #     # set progress
            #     context.scene.frame_set(progress)

            #     # take picture
            #     # TODO: modify path
            #     context.scene.render.filepath = path.join(filepath, 'simulation/image_{}.png'.format(progress))
            #     bpy.ops.render.render(write_still=True)

        cur_vtx = nl_vtx
        cur_pos = nl_pos

    print('Total Matches: {}/{}/{}'.format(num_valid_matches, num_matches, len(position)))
