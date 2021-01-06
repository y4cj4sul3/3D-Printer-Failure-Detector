import bpy
import argparse
from sys import argv
from sys import path as syspath
from os import path

import math
import numpy as np
from mathutils import Matrix
from datetime import datetime

def allInOne():
    then = datetime.now()

    # parse arguments
    pm, genTrain, genTest = getPathManager()

    # setup scene
    print('Setup Scene')
    setupScene(pm.abs(pm.camera_pos))

    # load model
    print('Load Model')
    verts, edges, time_height = loadModel(pm.abs(pm.model))

    # simulation
    print('Build Model')
    buildModel('Model', verts, edges, time_height)

    # generate training data
    if genTrain:
        print('Generate Training Data')
        genTrainingData(verts, edges, pm.abs(pm.progress), pm.abs(pm.training))
    
    # generate testing data
    if genTest:
        print('Generate Testing data')
        genTestingData(verts, edges, pm.abs(pm.testing))

    print('All done: ' + str(datetime.now()-then))


def getPathManager():
    # argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-path', '-a', type=str, required=True, help='Absolute path to project')
    parser.add_argument('--printer', '-p', type=str, required=True, help='Printer name')
    parser.add_argument('--printjob', '-j', type=str, required=True, help='Printer name')
    parser.add_argument('--gen-training-data', '-t', action='store_true', help='Printer name')
    parser.add_argument('--gen-testing-data', '-e', action='store_true', help='Printer name')

    try:
        idx = argv.index('--')
    except ValueError:
        print('No argument to parse')
        idx = 0

    args = parser.parse_args(argv[idx+1:])

    # get file path
    project_path = args.project_path
    printer_name = args.printer
    printjob_name = args.printjob
    genTrain = args.gen_training_data
    genTest = args.gen_testing_data
    print(project_path, printer_name, printjob_name)

    # import PathManager
    # FIXME: better not use sys.path
    syspath.append(project_path)
    from path_manager import PathManager

    pm = PathManager(abs_path=project_path, printer_name=printer_name, printjob_name=printjob_name)

    return pm, genTrain, genTest


def setupScene(filepath):
    # clear scene (delete default cube)
    if 'Cube' in bpy.data.objects:
        # deselect all
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['Cube'].select_set(True)
        bpy.ops.object.delete()

    # load camera pose
    if path.exists(filepath):
        with open(filepath, 'rb') as fp:
            camPos = np.load(fp, allow_pickle=True)
            bpy.data.objects['Camera'].matrix_world = Matrix(camPos)
    else:
        print('Config not found: ' + filepath)
        bpy.data.objects['Camera'].location = (0.25, -.02, 0.12)
        bpy.data.objects['Camera'].rotation_euler = (math.radians(80), 0, math.radians(45))

    # TODO: setup camera depends on printers
    bpy.data.objects['Camera'].data.lens = 33
    bpy.data.objects['Camera'].data.shift_x = 0.017
    bpy.data.objects['Camera'].data.shift_y = 0.04

    # TODO: rendering settings depends on printers
    bpy.context.scene.render.resolution_x = 495
    bpy.context.scene.render.resolution_y = 376
    bpy.context.scene.render.film_transparent = True


def loadModel(filepath):
    verts, edges, time_height = np.load(filepath, allow_pickle=True)
    return np.array(verts), np.array(edges), np.array(time_height)


def buildModel(name, verts, edges, time_height, collection_name='Collection'):
    # create mesh
    me = bpy.data.meshes.new(name)
    # reverse edge order
    edges_rev = np.flip(edges, 0)
    verts_resize = verts / 1000
    me.from_pydata(verts_resize.tolist(), edges_rev.tolist(), [])
    # build object
    model = bpy.data.objects.new(name, me)

    # Move into collection if specified
    if collection_name is not None:  # make argument optional
        # collection exists
        collection = bpy.data.collections.get(collection_name)
        if collection:
            bpy.data.collections[collection_name].objects.link(model)
        else:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(
                collection)  # link collection to main scene
            bpy.data.collections[collection_name].objects.link(model)

    # resize
    # model.scale /= 1000

    # select model
    bpy.ops.object.select_all(action='DESELECT')
    model.select_set(True)
    bpy.context.view_layer.objects.active = model

    # turn object into volumn (the operation take selected objects and active object)
    bpy.ops.object.convert(target='CURVE')
    model.data.bevel_depth = 0.000175

    # simulate slice
    frame_duration = len(edges)
    model.modifiers.new(name='Build', type='BUILD')
    model.modifiers["Build"].frame_duration = frame_duration
    bpy.context.scene.frame_end = frame_duration

    base_height = bpy.data.objects['Camera'].location[2]
    # set animation
    for frame, height in time_height:
        bpy.data.objects['Camera'].location[2] = base_height + height / 1000
        bpy.data.objects['Camera'].keyframe_insert(data_path="location", frame=frame, index=2)


def genTrainingData(verts, edges, progress_path, output_folder, layer_th=0.03, subdivide_th=1):
    # create folder

    # load progress
    timestamp = []
    # progress = []
    position = []
    with open(progress_path, 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            data = line.split(', ')
            if len(data) == 5:
                pos = [float(data[2][1:]), float(data[3]), float(data[4][:-2])]
                # if not np.isnan(pos).any():
                timestamp.append(float(data[0]))
                # progress.append(float(data[1]))
                position.append(pos)

    position = np.array(position)

    # loop each progress and find cooresponding frame by printhead position
    cur_pos = 0
    cur_vtx = 0
    cur_edge = 0
    num_pos = len(position)
    num_vtx = len(verts)

    # match the first layer
    # FIXME: ultimaker 3/3Ex may collect position > min z at beginning
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
        # print('Layer Height:', layer_height)
        # find the next layer index
        nl_pos = findNextLayerIndex(position, layer_height, cur_pos)
        nl_vtx = findNextLayerIndex(verts, layer_height, cur_vtx)
        # print(nl_pos - cur_pos, nl_vtx - cur_vtx)

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

        # print('Matches: {}/{}'.format(len(matches), nl_pos - cur_pos))
        num_matches += len(matches)

        if len(matches) > 0:
            # ascending check
            valid_matches = [matches[0]]    # assume first match is valid
            for i in range(1, len(matches)):
                if matches[i][1] > matches[i-1][1]:
                    valid_matches.append(matches[i])

            # print('Valid Matches: {}/{}'.format(len(valid_matches), len(matches)))
            num_valid_matches += len(valid_matches)

            for match in valid_matches:
                # find edge index, which is the frame index
                while edges[cur_edge, 1] < match[1]:
                    cur_edge += 1

                # render
                render(cur_edge, path.join(output_folder, '{}.png'.format(timestamp[match[0]])))

        cur_vtx = nl_vtx
        cur_pos = nl_pos

    # find edge index, which is the frame index
    # while edges[cur_edge][1] < valid_matches[-1][1]:
    #     cur_edge += 1
    # print(cur_edge, edges[cur_edge])

    # print(timestamp[valid_matches[-1][0]], valid_matches[-1][1])
    print('Total Matches: {}/{}/{}'.format(num_valid_matches, num_matches, len(position)))


def genTestingData(verts, edges, output_folder):
    # render for each layer (after move up)
    cur_vtx = 0
    cur_edge = 0
    num_vtx = len(verts)
    num_data = 0

    while cur_vtx < num_vtx:
        layer_height = round(verts[cur_vtx, 2]*100)/100

        # find next layer index
        cur_vtx = findNextLayerIndex(verts, layer_height, cur_vtx)

        # find edge index, which is the frame index
        while edges[cur_edge, 1] < cur_vtx:
            cur_edge += 1

        # render
        render(cur_edge, path.join(output_folder, '{}.png'.format(layer_height)))
        num_data += 1

    print('Total DATA:', num_data)

def findNextLayerIndex(pos, cur_height, start_idx=0, layer_th=0.03):
    nl_idx = start_idx
    num_pos = len(pos)
    while nl_idx < num_pos and pos[nl_idx, 2] - cur_height < layer_th:
        nl_idx += 1

    return nl_idx


def render(frame, filepath):
    # set progress
    bpy.context.scene.frame_set(frame)

    # render
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    allInOne()
