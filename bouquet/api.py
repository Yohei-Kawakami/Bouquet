# -*- coding: utf-8 -*-
def classify_movie_to_json(image_ar, scene_ar, video_path, json_name=None, category_model=None):
    """
    add classes of scene to json file
    """
    if not json_name:
        json_name = "material" # default name of json file
        
    print("before trying...")
    try:
        f = open(json_name + ".json", 'r')
        json_data = json.load(f)
        jsn = cl.OrderedDict(json_data)
        num_count = max(list(map(int, jsn.keys()))) + 1

    except:
        # make dictinary in order by collections.OrderedDict
        jsn = cl.OrderedDict()
        num_count = 0
    print("after trying...")

    image_ar = image_ar / 255.
    print(image_ar.shape)
    pred_proba = category_model.predict(image_ar, verbose=1)
    print("Finish to pred")

    for i in range(len(scene_ar)-1):
        arange_ar = np.arange(scene_ar[i], scene_ar[i + 1]).astype("int32")
        clas = np.argmax(np.sum(pred_proba[arange_ar, :], axis=0))
        pred_proba_one_class = pred_proba[arange_ar, clas].reshape(-1).tolist()
        # make a dictinary by OrderedDict
        data = cl.OrderedDict()
        data["path"] = video_path
        data["start"] = int(scene_ar[i])
        data["stop"] = int(scene_ar[i + 1])
        data["class"] = int(clas)
        data["classs_proba"] = pred_proba_one_class
        jsn[num_count] = data
        num_count += 1
        print("SceneNO:" + str(i) + "　Finish to classfy material")

    #writing json to a file with function: json.dump; I don't know why it doesn't work if I write twice.
    fw = open(json_name + ".json", 'w')
    json.dump(jsn, fw, indent=4)
    fw = open(json_name + ".json", 'w')
    json.dump(jsn, fw, indent=4)
    print("Finish to write json：")

def init_material_json(json_name):
    fw = open(json_name + ".json", 'w')
    json.dump("", fw, indent=4)
    fw = open(json_name + ".json", 'w')
    json.dump("", fw, indent=4)
    print("JSON is initialized!!：")

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

def get_num_scene_mtr(video_path):
    """
    Choose a number of scenes in as length of video: material network
    ----------
    The length of a scene is 9 second
    """
    image_ar = movie_to_image(video_path)
    video_span = image_ar.shape[0]/30

    if (video_span//9) -1 < 1:
        num_scene = 0
    elif 1 <= (video_span//9) -1 < 19:
        num_scene = (video_span//9) -1

    else:
        num_scene = 19
    return num_scene

def get_scene_movie_json(video_path, get_num_scene, json_name, category_model):
    """
    a main function of getting json information from video
    """
    image_ar = movie_to_image(video_path)
    num_scene = get_num_scene
    print("Make array from videos...")
    sabun_ar = background_subtraction(image_ar)
    scene_ar = get_choice_subtraction_index(sabun_ar, int(num_scene))
    print("Start to classify...")
    #scene_to_movie(scene_ar, video_path)
    classify_movie_to_json(image_ar, scene_ar, video_path, json_name, category_model)



def movie_to_image(video_path=None, num_cut=None, size=(150, 150)):
    """
    return frames of image as array if you give a path of video
    """
    if not num_cut:
        num_cut = 1
    if not video_path:
        video_path = "./material/material_video/material_video.mp4"
    
    # make an empty array
    video = []
    #size = (150, 150)
    frame_count = 0
    # read capture video（generate structure of capture）
    capture = cv2.VideoCapture(video_path)

    # loop while there are flames
    while(capture.isOpened()):
        # get a flame of the video
        ret, frame = capture.read()
        if ret == False:
            break

        # save frames of picture culled as the setting
        if frame_count % num_cut == 0:
            frame = cv2.resize(frame, size)
            #print(frame.shape)
            video.append(frame)

        frame_count += 1

    # open structure of capture
    capture.release()
    video_ar = np.array(video)

    # output Error if array is empty
    if not np.any(video_ar):
        raise Exception('The array is empty!')

    return video_ar

def background_subtraction(video_ar):
        """
        get a background subtraction of a video
        """
        sub = video_ar[:-1] - video_ar[1:]
        # calculate a mean of scenes: shape('a number of sample' -1,)
        subtraction_ar = np.mean(np.abs(sub.reshape(len(sub), -1)), axis=1)
        return subtraction_ar

def get_choice_subtraction_index(subtraction_ar, num_scene=None):
        """
        return splited scenes from background subtraction

        num_scene: int
            posts of divided: If 2 are given, it returns 3 scenes
        scene_ar:array shape(num_scene, )
            start from 0: (a number of frame to start, a number of frame to finish)
        """
        thresh_frame = 40 # a threshold of frames to cull

        # If num_scene is empty, it is finished.
        if not num_scene:
            scene_ar = np.array([0, len(subtraction_ar)])
            return scene_ar

        # a number of scenes-1
        arg_ind = np.argsort(-subtraction_ar)

        based_num_scene = 10
        # add scenes to based_num_scene if num_scene > based_num_scene
        if num_scene > based_num_scene:
            based_num_scene = num_scene + 5

        while len(arg_ind) >= based_num_scene:
            # pick up based num scenes from the top ofsabtraction(if it is needed more scenes, the loop add more them)
            arg_base_ind = arg_ind[:based_num_scene]
            sort_ind = np.sort(arg_base_ind)

            # delete index so near to each other
            for i in range(len(sort_ind)):
                try:
                    while True:
                        if (sort_ind[i + 1] - sort_ind[i]) <= thresh_frame:
                            sort_ind = np.delete(sort_ind, i + 1)
                        else:
                            break
                except IndexError:
                    break

            # delete index so near to starting point
            try:
                while True:
                    if sort_ind[0] <= thresh_frame:
                        sort_ind = np.delete(sort_ind, 0)
                    else:
                        break
            
            # delete index so near to end point
                while True:
                    if (len(subtraction_ar) - 1 - sort_ind[-1]) <= thresh_frame:
                        sort_ind = np.delete(sort_ind, -1)
                    else:
                        break
            except IndexError:
                    break

            # The roop is broken if picked up more than num_scene
            if len(sort_ind) >= num_scene:
                break
            else:
                based_num_scene += 5

        # arrange sort_ind in descending order
        scene_ar = np.zeros(len(arg_base_ind)) - 99
        for i in sort_ind:
            id = np.where(arg_base_ind == i)[0]
            scene_ar[id] = i
        scene_ar = np.delete(scene_ar, np.where(scene_ar == -99))
        scene_ar += 1  # the points of devided +1
        scene_ar = np.sort(scene_ar[:num_scene])  # pick up scenes and arrange in ascending order
        scene_ar = np.insert(scene_ar, 0, 0)  # Insert 0 to post of starting
        scene_ar = np.append(scene_ar,len(subtraction_ar))  # Insert a number of an end frame

        return scene_ar

    