# -*- coding: utf-8 -*-
import cv2
import numpy as np
from moviepy.editor import *
import json
from copy import deepcopy

class SynthesizeNetwork:

    def __init__(self):
        self.video_path = "./material/pro_material_mp4/pro_material.mp4"
        self.category_path = "./model/classfier_model.h5"
        self.num_cut = 1 #フレーム間の数　１なら全フレーム取得する
        
        
    def synthesizer(self, material_json, map_class=None, map_second=None):
        """
        動画合成
        """

        #map_classとmap_secondを読み込み
        if map_class.any() == None:
          map_class = [1, 1, 1, 0, 1, 2, 1, 1, 1, 5, 0, 5, 0, 0, 0, 5, 1, 1, 1, 1]
        
        if map_second.any() == None:
          map_second = [0.,0.86666667,2.8,6.56666667,9.76666667,12.16666667,
                    12.83333333, 16.66666667, 17.2,        22.1,        24.73333333, 26.96666667,
                    27.6,        29.8,        41.23333333, 43.16666667, 46.66666667, 51.23333333,
                    52.86666667, 57.76666667, 59.96666667]

        num_map = len(map_class)
        fw = open(material_json, 'r')
        material = json.load(fw) #辞書
        material_class = np.array([material[k]["class"] for k in material.keys()]) #数字のarray
        material_length_frame = np.array(
            [len(material[k]["classs_proba"]) for k in material.keys()])  #動画ごとのフレーム数

        Exclusion_ind_list = []
        export_ar = np.empty((0,3))

        for i in range(num_map):
            kaburimode = False
            material_del = deepcopy(material)
            print(material_del.keys())
            for d in Exclusion_ind_list:
                print(d)
                try:
                    del material_del[str(int(d))]
                except KeyError:
                    continue
            material_class_del = np.array([
                material_del[k]["class"] for k in material_del.keys()])  #数字のarray
            material_length_frame_del = np.array([
                len(material_del[k]["classs_proba"]) for k in material_del.keys()]) #動画ごとのフレーム数

            map_num_frame = int((map_second[i + 1] - map_second[i])*30)
            c_ind = np.where(material_class_del == map_class[i])[0]  #クラスがあるか
            l_ind = np.where(material_length_frame_del > map_num_frame)[0]  #長さが足りているか

            if not np.any(l_ind):  #ないなら被りおk状態になる
                print("被りありモード")
                kaburimode = True
                c_ind = np.where(material_class == map_class[i])[0]
                l_ind = np.where(material_length_frame > map_num_frame)[0]
            print(map_num_frame)
            ##ここから合致した動画を探す
            if not np.any(l_ind):
                print("素材の長さが足りないです　処理終了")
                break

            if not np.any(c_ind):
                if int(map_class[i]) in [2, 3, 4, 5, 6]:  #if ブツ撮り
                    print("ブツ撮りのその他のクラスへ割り当て")
                    if kaburimode:
                        c_ind = np.where(material_class >= 2)[0]
                    else:
                        c_ind = np.where(material_class_del >= 2)[0]

            if not np.any(c_ind):
                print("クラスなし適当に割り当て")
                c_ind = l_ind

            if np.any(c_ind) and np.any(l_ind):
                find_list = []
                for c in c_ind:
                    if c in l_ind:
                        find_list += [c]
                find_ar = np.array(find_list)

            if not np.any(find_ar):
                print("find_arなし適当に割り当て")
                find_ar = l_ind

            if kaburimode:
                sort_ind = np.argsort(material_length_frame)
            else:
                sort_ind = np.argsort(material_length_frame_del)

            optimum_ar = np.empty((0,2))
            for j in find_ar:
                for l, k in enumerate(sort_ind):
                    if j == k:
                        optimum_ar =np.vstack((optimum_ar, np.array([l, k])))
                        break
            optimum_ind = optimum_ar[np.argmin(optimum_ar[:, 0]), 1]

            if kaburimode:
                optimum_ind = str(int(optimum_ind))
            else:
                optimum_ind = list(material_del.keys())[int(optimum_ind)]

            ##ここから最適なフレームを抜き出す
            class_proba_ar = np.array(material[optimum_ind]["classs_proba"])
            print(len(class_proba_ar))
            print("map_num_frame")
            print(map_num_frame)
            ind_ar = np.array([np.arange(i, i + map_num_frame) for i in np.arange(0, len(class_proba_ar) - map_num_frame)])  #最後オーバーすると怖いので一応マイナス１
            start = (np.argmax(np.sum(class_proba_ar[ind_ar], axis=1))
                    + material[optimum_ind]["start"]) / 30  #一番確率が高いシーケンスの始まり秒
            end = start + map_second[i + 1] - map_second[i]
            #arrayに保存しておく
            export_ar = np.vstack((export_ar, np.array([optimum_ind, start, end]).reshape(1, 3)))
            #使用ずみの素材は除くためのリスト
            Exclusion_ind_list += [optimum_ind]

        #書き出し
        cliplist = []
        for i in range(len(export_ar)):
            print(i)
            cliplist += [
                VideoFileClip(
                    material[str(export_ar[i, 0])]["path"],
                    audio=False).subclip(
                        float(export_ar[i, 1]), float(export_ar[i, 2]))
            ]
        final_clip = concatenate_videoclips(cliplist)  #ビデオの接続
        audioclip = AudioFileClip("./material/pro_material_mp3/pro_material.mp3")
        final_clip = final_clip.set_audio(audioclip)
        final_clip.write_videofile("./output/Bouquet_Movie.mp4", fps=29)  # Many options...#書き込み