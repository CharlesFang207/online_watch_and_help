import sys
import os
import pickle
from pathlib import Path
import json
curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{curr_dir}/../virtualhome/virtualhome")
from simulation.unity_simulator import comm_unity
comm = comm_unity.UnityCommunication(port="8080", timeout_wait=150)
import pickle
import ipdb
directory = "full_dataset/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2"
files = os.listdir(directory)
files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
graph_file = open("/home/scai/Workspace/hshi33/virtualhome/online_watch_and_help/dataset/new_datasets/full_dataset.pik", "rb")
data = pickle.load(graph_file)
import re
sys.path.insert(0, f"{curr_dir}/../online_watch_and_help/")
from agents import language
sys.path.insert(0, f"{curr_dir}/")
def extract_episode_number(file_name):
    pattern = r'logs_episode\.(\d+)_iter\.\d+\.pik'
    
    match = re.search(pattern, file_name)
    
    if match:
        return (int)(match.group(1))
    else:
        return None
    
def convert_action(action_dict):
        script = ""
        if action_dict[0] is not None:
            script += "<char0> "
            script += action_dict[0]
        if action_dict[1] is not None:
            if action_dict[0] is not None:
                script += " | "
            script += "<char1> "
            script += action_dict[1]
        return script
count = 0
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
                1893, 1919, 3384, 564, 3090, 3324] #without language
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
    files.append("logs_episode.{}_iter.0.pik".format(episode_id))
for file in files:
    if file == "label.json":
        continue
    if (int)(file) in language_list:
        directory = "full_dataset/1500+episodes"
    else:
        directory = "full_dataset/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2"
    print(file)
    num = extract_episode_number(file)
    num_attempt = 1
    file1 = open(os.path.join(directory, file), "rb")
    plan_data = pickle.load(file1)
    if len(plan_data["obs"]) == 0:
        print("Improper Episode {}".format(num))
        continue

    if Path("../online_watch_and_help/path_sim_dev/video/{}".format(num)).is_dir():
        print("Episode {} already rendered".format(num))
        continue
    have_language = False
    for index, language in enumerate(plan_data["language"][0]):
        if language is not None:
            have_language = True
            break
    while num_attempt <= 1:
        try:

            comm.reset(data[num]["env_id"])
            print(data[num]["env_id"])
            print(data[num]["init_rooms"])

            s, message = comm.expand_scene(data[num]["init_graph"])
            comm.add_character('Chars/Male2', initial_room=data[num]["init_rooms"][0])
            if have_language:
                comm.add_character('Chars/Female4', initial_room=data[num]["init_rooms"][1])
            else:
                comm.add_character('Chars/Female4', initial_room="bathroom")

            print(s)
            for index, action in enumerate(plan_data["action"][0]):
                script = convert_action({0: action, 1: plan_data["action"][1][index]})
                print(script)
                if not have_language:
                    if action is None and plan_data["action"][1][index + 1] is not None:
                        with open("/home/scai/Workspace/hshi33/virtualhome/online_watch_and_help/path_sim_dev/video/{}/timemark.txt".format(num), "w") as file:
                            file.write("mark perspective change time")
                    comm.render_script([script], recording=True, frame_rate=10, camera_mode=["AUTO"],output_folder="video/", file_name_prefix="{}".format(num))
                else:
                    if plan_data["language"][0][index] is not None:
                        comm.render_script([script], recording=True, frame_rate=10, camera_mode=["AUTO"], output_folder="video/{}".format(num), file_name_prefix="language")
                        language_info = {0: plan_data["language"][0][index], 1: plan_data["language"][1][index]}
                        json_file_path = "/home/scai/Workspace/hshi33/virtualhome/online_watch_and_help/path_sim_dev/video/{}/language.json".format(num)
                        with open(json_file_path, "w") as json_file:
                            json.dump(language_info, json_file)
                    comm.render_script([script], recording=True, frame_rate=10, camera_mode=["AUTO"],output_folder="video/", file_name_prefix="{}".format(num))
            count += 1
            break
        except Exception as e:
            print("Episode {} failed to render in trail {}".format(num, num_attempt))
            print(str(e), type(e))
            comm = comm_unity.UnityCommunication(port="8080", timeout_wait=150)
            num_attempt += 1
    file1.close()
graph_file.close()

