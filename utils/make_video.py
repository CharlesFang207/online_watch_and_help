import cv2
import os
from pathlib import Path
import re
import json
import datetime
from moviepy.editor import ImageClip, concatenate_videoclips, TextClip, CompositeVideoClip, VideoFileClip, clips_array
from moviepy.config import change_settings
from PIL import Image, ImageDraw, ImageFont
import textwrap
os.environ["MAGICK_CONFIGURE_PATH"] = "/home/scai/Workspace/hshi33/virtualhome/data"
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
json_file = open("record.json", "r")
log_data = json.load(json_file)
caption = True
def extract_episode_number(file_name):
    pattern = r'logs_episode\.(\d+)_iter\.\d+\.pik'
    
    match = re.search(pattern, file_name)
    
    if match:
        return match.group(1)
    else:
        return None
def create_video_from_images(image_folder, video_path, fps, change_time):
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort() 

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_path = video_path.replace(".", "_before.")  
    video = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    perspective_change = False
    for image in images:
        temp = os.path.getctime(os.path.join(image_folder, image))
        image_time = datetime.datetime.fromtimestamp(temp)
        if image_time > change_time and not perspective_change:
            video.release()
            video_path = video_path.replace("before", "after")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  
            video = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        img_path = os.path.join(image_folder, image)
        frame = cv2.imread(img_path)
        video.write(frame)

    video.release()

    for image in images:
        os.remove(os.path.join(image_folder, image))

def add_text_to_image(image_path, text, output_path):
    image = Image.open(image_path).convert("RGBA")
    txt = Image.new("RGBA", image.size, (255, 255, 255, 0))

    # Initialize ImageDraw
    d = ImageDraw.Draw(txt)

    font = ImageFont.load_default()

    margin = 10
    max_width = image.width - 2 * margin
    wrapped_text = textwrap.fill(text, width=int(max_width / 10))  # Adjust width to fit the text in the image

    # Calculate total height of text block
    lines = wrapped_text.split('\n')
    line_height = d.textbbox((0, 0), 'A', font=font)[3]
    total_text_height = line_height * len(lines)
    y_text = image.height - total_text_height - margin  # Start from bottom with margin

    # Draw each line of text
    for line in lines:
        bbox = d.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        position = ((image.width - text_width) / 2, y_text)
        d.text(position, line, font=font, fill=(255, 255, 255, 255))
        y_text += line_height

    combined = Image.alpha_composite(image, txt)
    combined = combined.convert("RGB")  # Convert back to RGB mode

    combined.save(output_path)

def create_video_from_images_language(image_folder, video_path, fps, language_time, language_folder, text, video_path_2):
    # Get the list of images in the folder
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort()  # Sort images by name (ensure they are in the correct order)

    images_and_captions = []
    language_record = False
    for image in images:
        temp = os.path.getctime(os.path.join(image_folder, image))
        image_time = datetime.datetime.fromtimestamp(temp)
        if image_time > language_time and not language_record:
            language_record = True
            language_images = [img for img in os.listdir(language_folder) if img.endswith(".png")]
            language_images.sort()
            for img in language_images:
                images_and_captions.append((img, text))
        images_and_captions.append((image, None))

    
    output_images = []
    output_images2 = []
    for index, (image_path, caption) in enumerate(images_and_captions):
        # Create an ImageClip for the image
        if Path(os.path.join(image_folder, image_path)).is_file():
            image_path = os.path.join(image_folder, image_path)
        else:
            image_path = os.path.join(language_folder, image_path)
        if caption:
            output_image_path = f"temp_image_{index}.jpg"
            add_text_to_image(image_path, caption, output_image_path)
            output_images.append(output_image_path)
            output_images2.append(image_path)
        else:
            output_images.append(image_path)
            output_images2.append(image_path)

    clips = [ImageClip(img, duration=0.1) for img in output_images2]

    final_clip = concatenate_videoclips(clips, method="compose")

    final_clip.write_videofile(video_path_2, fps=fps)

    clips = [ImageClip(img, duration=0.1) for img in output_images]

    final_clip = concatenate_videoclips(clips, method="compose")

    final_clip.write_videofile(video_path, fps=fps)
    for img in output_images:
        if img.startswith("temp_image_"):
            os.remove(img)
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    for img in images:
        os.remove(os.path.join(image_folder, img))
    images = [img for img in os.listdir(language_folder) if img.endswith(".png")]
    for img in images:
        os.remove(os.path.join(language_folder, img))

directory = "../online_watch_and_help/path_sim_dev/video"
episode_list = [3437, 2709, 766, 1859, 404, 3367, 1917, 2726, 2808, 640, 549, 609, 538, 3289, 
                3096, 3412, 135, 2053, 801, 857, 144, 3128, 3082, 3325, 138, 3115, 3312, 3372, 
                2826, 642, 2719, 182, 3355, 3068, 153, 1827, 3031, 1797, 3056, 3179, 3462, 263, 
                221, 647, 557, 398, 1886, 784, 240, 3308, 913, 1931, 2079, 1134, 130, 3212, 3395, 
                634, 3058, 644, 1851, 395, 195, 3475, 202, 895, 1775, 3092, 3391, 780, 541, 407, 
                147, 865, 3197, 389, 128, 2448, 3157, 154, 628, 3117, 3371, 2447, 2780, 223, 3129, 
                1883, 212, 2070, 858, 393, 1856, 3438, 2584, 3292, 578, 1848, 2559, 2474, 571, 1802, 
                548, 1825, 225, 608, 218, 910, 2799, 956, 3145, 42, 193, 2462, 3366, 211, 1758, 161, 
                1818, 1867, 2801, 3081, 949, 406, 3300, 3533, 3419, 397, 630, 956, 417, 3130, 3315, 
                612, 3098, 3074, 2829, 1798, 121, 3166, 2473, 240, 892, 2701, 149, 905, 801, 1861, 3119, 
                179, 3398, 869, 1131, 129, 1817, 871, 2748, 1140, 1894, 3423, 3328, 532, 2512, 854, 583, 
                1819, 949, 1892, 152, 1880, 655, 824, 3080, 906, 3063, 2759, 1811, 2542, 2050, 3077, 550, 
                650, 577, 2813, 3070, 790, 1858, 848, 3050, 3433, 1860, 767, 3060, 3478, 3047, 3344, 3065, 
                569, 528, 682, 2045, 2624, 931, 1865, 3323, 3140, 1765, 1813, 2556, 3536, 601, 2536, 931, 
                1893, 1919, 3384, 564, 3090, 3324] #without langauge
language_list = [2996, 87, 3169, 713, 259, 1185, 363, 707, 523, 588, 822, 2786, 527, 1676, 2260, 847, 
                 859, 1644, 529, 1149, 1035, 1681, 1638, 1036, 3155, 1361, 1261, 662, 1338, 3131, 1217, 
                 2259, 1308, 1127, 1102, 1218, 1871, 13, 3026, 1753, 771, 2617, 1717, 1821, 204, 1343, 
                 109, 709, 1459, 97, 710, 1322, 1043, 1299, 1307, 1116, 1997, 812, 3446, 835, 1443, 
                 2169, 2063, 2383, 3447, 2615, 2765, 2110, 2703, 1206, 3426, 1143, 1671, 567, 3429, 
                 3041, 722, 545, 852, 3303, 1702, 247, 2425, 3091, 2101, 1021, 1365, 556, 327, 1155, 
                 1452, 1378, 1783, 918, 1518, 2876, 2689, 29, 2459, 714, 1358, 2263, 1091, 1506, 1071, 
                 269, 3180, 1141, 2881, 270, 2966, 71, 636, 1254, 2470, 35, 2431, 782, 2311, 774, 595, 
                 1212, 1277, 2783, 3404, 2019, 2577, 1421, 1294, 486, 593, 2548, 786, 1311, 2511, 442, 
                 3364, 1385, 2681, 3270, 1458, 2714, 1636, 2547, 2305, 2946, 1730, 2290, 875, 813, 2845, 
                 1374, 1366, 2573, 1089, 657, 2797, 3014, 2527, 1341, 242, 2482, 1444, 2791, 898, 450, 
                 3053, 1059, 275, 1129, 2494, 643, 3073, 521, 2947, 1291, 1253, 3071, 615, 1419, 423, 
                 1899, 1363, 1635, 1015, 1909, 1073, 2851, 279, 543, 941, 1293, 243, 2811, 613, 1433, 
                 1907, 3479, 907, 1791, 539, 1591, 2705, 807, 1313, 843, 881, 685, 1309, 271, 347, 803, 
                 658, 1409, 337, 3209] #with language
episode_list += language_list
files = []
for episode_id in episode_list:
    files.append(str(episode_id))
for file in files:
    render = True
    '''for file_name in log_data["failed_files"]:
        if (int)(file) == file_name:
            print("episodes {} has failed to render".format(file))
            images = [img for img in os.listdir(os.path.join(directory, file, "0")) if img.endswith(".png")]
            for image in images:
                os.remove(os.path.join(directory, file, "0", image))
            images = [img for img in os.listdir(os.path.join(directory, file, "1")) if img.endswith(".png")]
            for image in images:
                os.remove(os.path.join(directory, file, "1", image))
            render = False
            break'''
    if not render:
        continue
    if Path(os.path.join(directory, file, 'character0.mp4')).is_file():
        print("video of episode {} was produced".format(file))
        continue
    if Path(os.path.join(directory, file, "episode_{}.mp4".format(file))).is_file():
        print("video of episode {} was produced".format(file))
        continue
    print("Producing video of episode {}".format(file))
    if Path(os.path.join(directory, file, "language.json")).is_file() and caption:
        with open(os.path.join(directory, file, "language.json"), "r") as json_file:
            language_info = json.load(json_file)
        temp = os.path.getctime(os.path.join(directory, file, "language"))
        language_time = datetime.datetime.fromtimestamp(temp)
        image_folder = os.path.join(directory, file, "0")
        language_folder = os.path.join(directory, file, "language", "0")
        video_path_0 = os.path.join(directory, file, 'character0_caption.mp4')
        video_path_0_2 = os.path.join(directory, file, 'character0.mp4')
        fps = 10
        print(language_info)
        create_video_from_images_language(image_folder, video_path_0, fps, language_time, language_folder, language_info['0'], video_path_0_2)

        image_folder = os.path.join(directory, file, "1")
        language_folder = os.path.join(directory, file, "language", "1") 
        video_path_1 = os.path.join(directory, file, 'character1_caption.mp4')
        video_path_1_2 = os.path.join(directory, file, 'character1.mp4')
        fps = 10

        create_video_from_images_language(image_folder, video_path_1, fps, language_time, language_folder, language_info['1'], video_path_1_2)

        '''video1 = VideoFileClip(video_path_0)
        video2 = VideoFileClip(video_path_1)
        final_clip = clips_array([[video1, video2]])
        final_clip.write_videofile(os.path.join(directory, file, "episode_{}.mp4".format(file)))'''
    elif Path(os.path.join(directory, file, "timemark.txt").is_file()):
        image_folder = os.path.join(directory, file, "0") 
        video_path_0 = os.path.join(directory, file, 'character0.mp4')
        temp = os.path.getctime(os.path.join(directory, file, "timemark.txt"))
        change_time = datetime.datetime.fromtimestamp(temp)
        fps = 10

        create_video_from_images(image_folder, video_path_0, fps, change_time)

        image_folder = os.path.join(directory, file, "1") 
        video_path_1 = os.path.join(directory, file, 'character1.mp4')
        fps = 10

        create_video_from_images(image_folder, video_path_1, fps, change_time)

        '''video1 = VideoFileClip(video_path_0)
        video2 = VideoFileClip(video_path_1)
        final_clip = clips_array([[video1, video2]])
        final_clip.write_videofile(os.path.join(directory, file, "episode_{}.mp4".format(file)))'''
    else:
        raise Exception("problem in rendering procedure for episode {}".format(file))