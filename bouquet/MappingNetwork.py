# -*- coding: utf-8 -*
import __init__
import keras
from keras import models
import scipy.stats as stats
import cv2
import numpy as np
import collections as cl
import json

def init_material_json(json_name):
    fw = open(json_name + ".json", 'w')
    json.dump("", fw, indent=4)
    fw = open(json_name + ".json", 'w')
    json.dump("", fw, indent=4)
    print("json初期化完了：")


def get_num_scene_map(video_path):
    """
    動画から取り出すシーン数を決める
    """
    image_ar = movie_to_image(video_path)
    video_span = image_ar.shape[0]/30

    if (video_span//3) -1 < 1:
        num_scene = 0
    elif 1 <= (video_span//3) -1 < 19:
        num_scene = (video_span//5) -1

    else:
        num_scene = 19
    return num_scene

def movie_to_image(video_path=None, num_cut=None, size=(150, 150)):
        #動画のパスを渡すとnum_cut(フレーム)ごとの画像をarrayにして返す

        if not num_cut:
            num_cut = 1
        if not video_path:
            video_path = "./material/material_video/material_video.mp4"

        video = []
        #size = (150, 150)
        frame_count = 0
        # キャプチャ動画読み込み（キャプチャ構造体生成）
        capture = cv2.VideoCapture(video_path)

        # フレーム画像がある限りループ
        while(capture.isOpened()):
            # フレーム画像一枚取得
            ret, frame = capture.read()
            if ret == False:
                break

            # 指定した数だけフレーム画像を間引いて保存
            if frame_count % num_cut == 0:
                frame = cv2.resize(frame, size)
                #print(frame.shape)
                video.append(frame)

            frame_count += 1

        # キャプチャ構造体開放
        capture.release()
        video_ar = np.array(video)

        #配列が空ならエラーにする
        if not np.any(video_ar):
            raise Exception('配列が空です!')

        return video_ar

def get_scene_movie_json(video_path, get_num_scene, json_name, category_model):
    """
    動画をシーンで分類しジェイソンファイルを作成するまでまとめたやつ
    """
    image_ar = movie_to_image(video_path)
    num_scene = get_num_scene
    print("ビデオをイメージ化済...")
    sabun_ar = background_subtraction(image_ar)
    scene_ar = get_choice_subtraction_index(sabun_ar, int(num_scene))
    print("分類開始...")
    #scene_to_movie(scene_ar, video_path)
    classify_movie_to_json(image_ar, scene_ar, video_path, json_name, category_model)


def classify_movie_to_json(image_ar, scene_ar, video_path, json_name=None, category_model=None):
    """
    素材一覧のjsonファイルを作る
    """
    if not json_name:
        json_name = "material" #jsonファイルの名前
        
    print("try前...")
    try:
        f = open(json_name + ".json", 'r')
        json_data = json.load(f)
        jsn = cl.OrderedDict(json_data)
        num_count = max(list(map(int, jsn.keys()))) + 1

    except:
        #collections.OrderedDictで順序を指定した辞書を作成
        jsn = cl.OrderedDict()
        num_count = 0
    print("try後...")

    image_ar = image_ar / 255.
    print(image_ar.shape)
    pred_proba = category_model.predict(image_ar, verbose=1)
    print("pred完了")

    for i in range(len(scene_ar)-1):
        arange_ar = np.arange(scene_ar[i], scene_ar[i + 1]).astype("int32")
        clas = np.argmax(np.sum(pred_proba[arange_ar, :], axis=0))
        pred_proba_one_class = pred_proba[arange_ar, clas].reshape(-1).tolist()
        #辞書の作成
        data = cl.OrderedDict()
        data["path"] = video_path
        data["start"] = int(scene_ar[i])
        data["stop"] = int(scene_ar[i + 1])
        data["class"] = int(clas)
        data["classs_proba"] = pred_proba_one_class
        jsn[num_count] = data
        num_count += 1
        print(str(i) + "シーン目　素材分類完了")

    #json.dump関数でファイルに書き込む 二回やらないとなぜかうまく書き込めない
    fw = open(json_name + ".json", 'w')
    json.dump(jsn, fw, indent=4)
    fw = open(json_name + ".json", 'w')
    json.dump(jsn, fw, indent=4)
    print("json書き出し完了：")



def background_subtraction(video_ar):
        #背景差分をとる関数
        sub = video_ar[:-1] - video_ar[1:]
        #maeの計算 shape(sample数-1,)
        subtraction_ar = np.mean(np.abs(sub.reshape(len(sub), -1)), axis=1)
        return subtraction_ar


def get_choice_subtraction_index(subtraction_ar, num_scene=None):
        """
        背景差分を渡すと、シーン分割のインデックスを返す関数

        num_scene: int
            シーンの分かれ目の欲しい数　2ならシーンとしては3になります
        scene_ar:array shape(num_scene, )
            0から始まる。各値はシーンの開始フレーム, 動画の最終フレーム
        """
        thresh_frame = 40 #間を開けるフレームの閾値

        #ゼロなら処理終了
        if not num_scene:
            scene_ar = np.array([0, len(subtraction_ar)])
            return scene_ar

        arg_ind = np.argsort(-subtraction_ar)
        kari_num_scene = 10
        #kari_num_sceneが希望する分割数より少ない場合増やす
        if num_scene > kari_num_scene:
            kari_num_scene = num_scene + 5

        while len(arg_ind) >= kari_num_scene:
            #とりあえず差分上位１０個だけ抜き出す,足りないならループで増やす
            arg_kari_ind = arg_ind[:kari_num_scene]
            sort_ind = np.sort(arg_kari_ind)

            #秒数が近いインデックスは消す 閾値15フレーム
            for i in range(len(sort_ind)):
                try:
                    while True:
                        if (sort_ind[i + 1] - sort_ind[i]) <= thresh_frame:
                            sort_ind = np.delete(sort_ind, i + 1)
                        else:
                            break
                except IndexError:
                    break

            #動画の最初から0.5秒空いてないとそのインデックスは消す
            try:
                while True:
                    if sort_ind[0] <= thresh_frame:
                        sort_ind = np.delete(sort_ind, 0)
                    else:
                        break
            
            #動画の最後から0.5秒空いてないとそのインデックスは消す
                while True:
                    if (len(subtraction_ar) - 1 - sort_ind[-1]) <= thresh_frame:
                        sort_ind = np.delete(sort_ind, -1)
                    else:
                        break
            except IndexError:
                    break

            #num_sceneより多くシーンが抜き出せていればbreakする
            if len(sort_ind) >= num_scene:
                break
            else:
                kari_num_scene += 5

        #昇順になっているsort_indを差分降順に直す
        scene_ar = np.zeros(len(arg_kari_ind)) - 99
        for i in sort_ind:
            id = np.where(arg_kari_ind == i)[0]
            scene_ar[id] = i
        scene_ar = np.delete(scene_ar, np.where(scene_ar == -99))
        scene_ar += 1  #差分なのでシーンの分かれ目はプラス１になる
        scene_ar = np.sort(scene_ar[:num_scene])  #シーンを取り出し後昇順に並び替える
        scene_ar = np.insert(scene_ar, 0, 0)  #ぜろを先頭に挿入
        scene_ar = np.append(scene_ar,len(subtraction_ar))  #動画の最終フレーム数を最後に挿入

        return scene_ar


class MappingNetwork:
    def __init__(self):
        self.video_path = "./material/pro_material_mp4/pro_material.mp4"
        self.category_path = "./model/classfier_model.h5"
        self.num_cut = 1 #フレーム間の数　１なら全フレーム取得する


    def mapping(self, file_dir, init=True, category_model=None, json_name='mapping'):
        
        if init:
            init_material_json(json_name)
            
        num_scene = get_num_scene_map(file_dir)
        get_scene_movie_json(file_dir, num_scene, json_name, category_model)