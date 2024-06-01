import pickle
import sys
import os
import re
import json
import ipdb
import random
curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{curr_dir}/../online_watch_and_help/")
from agents import language
sys.path.insert(0, f"{curr_dir}/")
def parse_string(s):
    # Define a regular expression pattern to match the parts of the string
    pattern = r'\[(.*?)\] <(.*?)> \((\d+)\) <(.*?)> \((\d+)\)'
    match = re.match(pattern, s)
    
    if match:
        # Extract the parts and convert the number to an integer
        action = match.group(1)
        device = match.group(2)
        number = match.group(3)
        device1 = match.group(4)
        number1 = match.group(5)
        return [action, device, number, device1, number1]
    
    else:
        # If the pattern does not match, return an empty list or raise an error
        pattern1 = r'\[(.*?)\] <(.*?)> \((\d+)\)'
        match = re.match(pattern1, s)
        if match:
            action = match.group(1)
            device = match.group(2)
            number = match.group(3)
            return [action, device, number]

#directory = "/home/scai/Workspace/sye10/virtualHome/data/train_env_task_set_2_full_task.all_apts.0,1,2,4,5/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2/"
directory = "full_dataset/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2"
files = os.listdir(directory)
files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
valid_files = []
dict = {}
for file in files:
    try:
        file1 = open(os.path.join(directory, file), "rb")
        data = pickle.load(file1)
        if data["obs"] == []:
            continue
        goal_0 = data["goals"][0]
        goal_1 = data["goals"][1]
        dict[file] = []
        for index, action in enumerate(data["action"][1]):
            if action == None:
                continue
            predicate = parse_string(action)
            if predicate[0] in ["putin", "putback"]:
                for k, v in goal_0.items():
                    goal_place = k.split("_")[2]
                    if predicate[4] == goal_place and (int)(predicate[2]) in v["grab_obj_ids"]:
                        if "help" not in dict[file]:
                            dict[file].append("help")
            if predicate[0] == "grab":
                if index == 0:
                    continue
                state = data["graph"][index - 1]
                for k, v in goal_0.items():
                    '''if k == "on_spoon_199" and index == 15 and file == "logs_episode.3_iter.0.pik":
                        ipdb.set_trace()''' 
                    goal_place = k.split("_")[2]
                    if (int)(predicate[2]) in v["grab_obj_ids"]:
                        for edge in state["edges"]:
                            '''if edge == {"from_id": 341, "to_id": 199, "relation_type": "ON"}:
                                ipdb.set_trace()'''
                            if edge["from_id"] == (int)(predicate[2]) and edge["to_id"] == (int)(goal_place) and edge["relation_type"] == k.split("_")[0].upper():
                                if "hinder" not in dict[file]:
                                    dict[file].append("hinder") 
            if data["language"][1][index] is not None:
                if data["language"][1][index].try_to_hinder: #this language attempt to hinder
                    if "try_to_hinder" not in dict[file]:
                        dict[file].append("try_to_hinder")
                        for obj_name, info in data["language"][1][index].obj_positions.items(): #enumerate all information provided to see if provide information match actual graph
                            for obj_id, places in info.items():
                                for place in places:
                                    if place["position"] is not None:
                                        edge_provide = {"from_id": obj_id, "to_id": place["position"], "relation_type": place["predicate"].upper()}
                                        state = data["graph"][index - 1]
                                        if edge_provide in state["edges"]:
                                            if "failed_hinder" not in dict[file]:
                                                dict[file].append("failed_hinder")
                                            elif "successful_hinder" not in dict[file]:
                                                dict[file].append("successful_hinder")
                else:
                    '''help = False
                    for obj_name, info in data["language"][1][index].obj_positions.items():
                        ipdb.set_trace()
                        for obj_id, places in info.items():
                            if len(places) > 0:
                                help = True'''
                    if "try_to_help" not in dict[file] and help:
                        dict[file].append("try_to_help")
                        for obj_name, info in data["language"][1][index].obj_positions.items(): #enumerate all information provided to see if provide information match actual graph
                            for obj_id, places in info.items():
                                for place in places:
                                    if place["position"] is not None:
                                        edge_provide = {"from_id": obj_id, "to_id": place["position"], "relation_type": place["predicate"].upper()}
                                        state = data["graph"][index - 1]
                                        if edge_provide in state["edges"]:
                                            if "successful_help" not in dict[file]:
                                                dict[file].append("successful_help")
                                            elif "failed_help" not in dict[file]:
                                                dict[file].append("failed_help")
    except pickle.UnpicklingError as e:
        print(str(e))
        ipdb.set_trace()
        continue
print(dict)
for file in files:
    if file in dict.keys() and "help" in dict[file]:
        temp = open(os.path.join(directory, file), "rb")
        data = pickle.load(temp)
        print(file, data["env_id"])
with open(os.path.join(directory, "label.json"), "w") as json_file:
    json.dump(dict, json_file, indent=4)


