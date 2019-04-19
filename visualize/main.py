# -*- coding: utf-8 -*-

import __init__
from pytube import YouTube
import sys
import os

import moviepy.editor as mpe

import glob
import tkinter
from tkinter import *
import tkinter as tk, threading
import imageio
from PIL import Image, ImageTk

#エラーメッセージ
__ERROR_MESSAGE__ = None

# 動画を流す
def stream(label):
    # 表示する動画
    video_name = "./views/wedding1.mp4"
    video = imageio.get_reader(video_name)
    for image in video.iter_data():
        frame_image = ImageTk.PhotoImage(Image.fromarray(image).resize((528, 352),Image.ANTIALIAS))
        label.config(image=frame_image)
        label.image = frame_image

#Youtubeの動画をダウンロードする
def get_youtube(y_url,download_location,audio_only_flg):
    #一旦エラーメッセージをクリア
    __ERROR_MESSAGE__ = None

    #URLの入力に関する例外処理
    if type(y_url) != str or y_url == "" :
        __ERROR_MESSAGE__ = "URLには文字列を入れてください"

    #「http://」が省略されて入れば付け加える
    if not (y_url.startswith("http://") or y_url.startswith("https://")):
        y_url = "http://" + y_url
    #ダウンロード先フォルダが省略されて入れば、カレントディレクトリに設定

    # 素材動画のダウンロード先
    download_location_mp4 = "./material/pro_material_mp4"
    download_location_mp3= "./material/pro_material_mp3"

    #エラーメッセージが出ていなければ動画を取得する
    if __ERROR_MESSAGE__ == None:
        youtube = YouTube(y_url)
        
        #動画をダウンロード
        try:
            youtube.streams.filter(subtype='mp4').first().download(download_location_mp4)
            
        except FileNotFoundError:
            os.mkdir(material/download_location_mp4)
            youtube.streams.filter(subtype='mp4').first().download(download_location_mp4)
        
        file1 = glob.glob('{}/*.*mp4'.format(download_location_mp4))

        # 動画変更前ファイル
        path1 = file1[1]
        # 動画変更後ファイル
        path2= '{}/pro_material.mp4'.format(download_location_mp4)
        # 動画ファイル名の変更 
        os.rename(path1, path2) 

        #音声をダウンロード
        try:
            youtube.streams.filter(only_audio=True).first().download(download_location_mp3)

        except FileNotFoundError:
            os.mkdir(material/download_location_mp3)
            youtube.streams.filter(only_audio=True).first().download(download_location_mp3)

        file2 = glob.glob('{}/*.*'.format(download_location_mp3))
        
        # 動画変更前ファイル
        path1 = file2[0]
        # 動画変更後ファイル
        path2= '{}/pro_material.mp3'.format(download_location_mp3)
        
        # 動画ファイル名の変更 
        video = mpe.VideoFileClip(path1)
        video.audio.write_audiofile(path2)
        
#画面の表示
def main():
    root = Tk()
    root['bg'] = "#FFF0F5"

    #タイトル
    root.title('Bouquet: Wedding Movie Maker')
    root.minsize(900, 100)

    # 商品名
    label0 = Label(text='"Bouquet for Wedding Movies"', font=(u'Garamond', 19, 'italic', 'bold'), background="#FFF0F5")
    label0.pack(pady=10)
    
    # 表示用動画を流す
    my_label = Label(root)
    my_label.pack()
 
    thread = threading.Thread(target=stream, args=(my_label,))
    thread.daemon = 1
    thread.start()

    #プロの動画
    label1 = Label(text="A Video of Professonal:Youtube(Optional)", font=(u'Garamond', 12, 'italic'), background="#FFF0F5")
    label1.pack(pady=10)

    # プロ動画入力メッセージ
    __PRO_MESSAGE__ = u'Insert Video URL on Youtube'

    #urlボックス
    y_url_box = Entry(width=40)
    y_url_box.insert(tk.END, __PRO_MESSAGE__)
    y_url_box.pack()

    #ロケーションボックスのラベル
    label99 = Label(text="Save Edited Movie in Your Folder(Optional)", font=(u'Garamond', 12, 'italic'), background="#FFF0F5")
    label99.pack(pady=5)

    # 出力保存フォルダメッセージ
    __SAVE_MESSAGE__ = u'' #'Insert a Folder Path'

    #ロケーションボックス1
    download_location_box = Entry(width=40)
    download_location_box.insert(tk.END, __SAVE_MESSAGE__)
    download_location_box.pack()

    #ユーザーの動画
    label1 = Label(text="▼▼▼ Insert Your Video on Youtube ▼▼▼", font=(u'Garamond', 12, 'bold', 'italic'), background="#FFF0F5")
    label1.pack(pady=10)

    # 素材動画入力メッセージ
    __URL_MESSAGE__ = u'' # Insert Video URL on Youtube
    
    #urlボックス1
    y_url1_box = Entry(width=40)
    y_url1_box.insert(tk.END, u'')
    y_url1_box.pack()

    #urlボックス2
    y_url2_box = Entry(width=40)
    y_url2_box.insert(tk.END,  __URL_MESSAGE__)
    y_url2_box.pack()

    #urlボックス3
    y_url3_box = Entry(width=40)
    y_url3_box.insert(tk.END,  __URL_MESSAGE__)
    y_url3_box.pack()

    #urlボックス4
    y_url4_box = Entry(width=40)
    y_url4_box.insert(tk.END,  __URL_MESSAGE__)
    y_url4_box.pack()

    #urlボックス5
    y_url5_box = Entry(width=40)
    y_url5_box.insert(tk.END,  __URL_MESSAGE__)
    y_url5_box.pack()

    #urlボックス(1~5)
    material_urls = [y_url1_box.get(), y_url2_box.get(), y_url3_box.get(), y_url4_box.get(), y_url5_box.get()]

    #オーディオボタン
    chk_state = BooleanVar()
    chk_state.set(False) 
    # chk = Checkbutton(text='Only Music', var=chk_state, background="#FFF0F5")
    # chk.pack(pady=10)

    #ダウンロードボタン
    InputButton = Button(text="Make Video",command = lambda : get_youtube(y_url_box.get(),download_location_box.get(),chk_state.get()))
    InputButton.pack(pady=20)

    #エラーメッセージ表示欄
    label99 = Label(text=__ERROR_MESSAGE__)
    label99.pack(pady=30)

    root.mainloop()

if __name__ == "__main__":
    main()