# -*- coding: utf-8 -*-
import cv2
import numpy as np
from moviepy.editor import *
import json
from copy import deepcopy

class SynthesizeNetwork:
    '''
    SynthesizeNetwork 
    make a edited video from materials as map(pro movie if chosen). 

　   input: material.json, map_class, map_second
     output: a synthesized video

    Parameter & Attribute
    ---------------------------------------
    material_json: json object
　  map_class: list object
　  map_second: list object

    '''

    def __init__(self):
        self.video_path = "./material/pro_material_mp4/pro_material.mp4"
        self.category_path = "./model/classfier_model.h5"
        self.num_cut = 1 # number of frames; "1" is all flames
        
        
    def synthesizer(self, material_json, map_class=None, map_second=None):
        """
        動画合成
        """

        # import mapping information
        if map_class.any() == None:
          map_class = [1, 1, 1, 0, 1, 2, 1, 1, 1, 5, 0, 5, 0, 0, 0, 5, 1, 1, 1, 1]
        
        if map_second.any() == None:
          map_second = [0.,0.86666667,2.8,6.56666667,9.76666667,12.16666667,
                    12.83333333, 16.66666667, 17.2,        22.1,        24.73333333, 26.96666667,
                    27.6,        29.8,        41.23333333, 43.16666667, 46.66666667, 51.23333333,
                    52.86666667, 57.76666667, 59.96666667]

        num_map = len(map_class) # numbers of scene
        
        # import material information
        fw = open(material_json, 'r')
        material = json.load(fw) # dictinary of material
        material_class = np.array([material[k]["class"] for k in material.keys()]) # class of scene
        material_length_frame = np.array(
            [len(material[k]["classs_proba"]) for k in material.keys()])  # numbers of scene

        exclusion_class_list = [] # used material
        export_ar = np.empty((0,3))

        for i in range(num_map):
            duplicated_mode = False
            material_del = deepcopy(material) # type of dictionary
            print(material_del.keys())
            for d in exclusion_class_list:
                print(d)
                # delete material which class is in  exclusion_class_list
                try:
                    del material_del[str(int(d))]
                except KeyError:
                    continue
            material_class_del = np.array([
                material_del[k]["class"] for k in material_del.keys()])  # Class list which was not deleted
            material_length_frame_del = np.array([
                len(material_del[k]["classs_proba"]) for k in material_del.keys()]) # numbers of scene

            # scene of map
            map_num_frame = int((map_second[i + 1] - map_second[i])*30) # caluculate in order
            c_ind = np.where(material_class_del == map_class[i])[0]  # Is there the class?? ==> if true:array[...], if false:array[]
            l_ind = np.where(material_length_frame_del > map_num_frame)[0]  # Does the scene have enough length?? ==> if true:array[...], if false:array[]

            if not np.any(l_ind):  # migrate to mode of dublicated if not enough length
                print("Mode of dublicated")
                duplicated_mode = True
                c_ind = np.where(material_class == map_class[i])[0] # search from original
                l_ind = np.where(material_length_frame > map_num_frame)[0] # search from original
            print(map_num_frame)

            ## searching matchinig videos
            if not np.any(l_ind):
                print("Error :There are not any scenes of material that have enough length")
                break 

            # class: still life photography
            if not np.any(c_ind):
                if int(map_class[i]) in [2, 3, 4, 5, 6]:  #if class is in still_life_photography group
                    print("Migrate to other class in still life photography")
                    if duplicated_mode:
                        c_ind = np.where(material_class >= 2)[0] # seach from original
                    else:
                        c_ind = np.where(material_class_del >= 2)[0] # search from deleted
            
            # class: view or face
            if not np.any(c_ind):
                print("No class: Migrate to any other class")
                c_ind = l_ind
            
            # Normal processing
            if np.any(c_ind) and np.any(l_ind):
                find_list = []
                for c in c_ind:
                    if c in l_ind:
                        find_list += [c]
                find_ar = np.array(find_list)

            if not np.any(find_ar):
                print("No find_ar: Migrate to any other class")
                find_ar = l_ind

            # sort out in order to material length
            if duplicated_mode:
                sort_ind = np.argsort(material_length_frame)
            else:
                sort_ind = np.argsort(material_length_frame_del) # Normal Processing

            # store positional information into array
            optimum_ar = np.empty((0,2))
            for j in find_ar: # j: position in class list
                for l, k in enumerate(sort_ind): # l: position in list: ascending order, k: rank of length in list
                    if j == k:
                        optimum_ar =np.vstack((optimum_ar, np.array([l, k])))
                        break

            optimum_ind = optimum_ar[np.argmin(optimum_ar[:, 0]), 1]

            if duplicated_mode:
                optimum_ind = str(int(optimum_ind))
            else:
                optimum_ind = list(material_del.keys())[int(optimum_ind)] # Normal Processing

            ## choose optimal scene
            class_proba_ar = np.array(material[optimum_ind]["classs_proba"]) # choose a specific scene
            print(len(class_proba_ar))
            print("map_num_frame")
            print(map_num_frame)
            ind_ar = np.array([np.arange(i, i + map_num_frame) for i in np.arange(0, len(class_proba_ar) - map_num_frame)])  # -1: for last scene in material
            start = (np.argmax(np.sum(class_proba_ar[ind_ar], axis=1))
                    + material[optimum_ind]["start"]) / 30  # highest proba second which a scene starts
            end = start + map_second[i + 1] - map_second[i]
            # save as array
            export_ar = np.vstack((export_ar, np.array([optimum_ind, start, end]).reshape(1, 3)))
            # delete used class from deleted class
            exclusion_class_list += [optimum_ind]

        # export to movie
        cliplist = []
        for i in range(len(export_ar)):
            print(i)
            cliplist += [
                VideoFileClip(
                    material[str(export_ar[i, 0])]["path"],
                    audio=False).subclip(
                        float(export_ar[i, 1]), float(export_ar[i, 2]))
            ]
        final_clip = concatenate_videoclips(cliplist)  # combine scenes
        audioclip = AudioFileClip("./material/pro_material_mp3/pro_material.mp3")
        final_clip = final_clip.set_audio(audioclip)
        final_clip.write_videofile("./output/Bouquet_Movie.mp4", fps=30)  # Many options...