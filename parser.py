import pickle
import numpy as np

folderPath = 'data/UM3/UM3_lead_screw_hold_20201129151229/'

with open(folderPath + 'printJob_finish.pkl', 'rb') as fp:
    print(pickle.load(fp))

# with open(folderPath + 'progress.pkl', 'rb') as fp:
#     print(pickle.load(fp))

