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

def generate_belief_goal(data, index): #data: record in pickle of interaction; index: steps upto for accounting
    knowledge = []
    for step in range(0, index):
        if data["language_object"][0][step] is not None: #agent 0 asked for help at the step
            for obj in data["language_object"][0][step].obj_list:
                if obj not in knowledge:
                    knowledge.append(obj)
    return knowledge

def check_information(graph, edge):
    obj_id = edge["from_id"]
    predicate = edge["relation_type"]
    position = edge["to_id"]
    class_name = ""
    for node in graph["nodes"]:
        if node["id"] == obj_id:
            class_name = node["class_name"]
    objs = [node["id"] for node in graph["nodes"] if node["class_name"] == class_name]
    for edge1 in graph["edges"]:
        if edge1["from_id"] in objs and edge1["to_id"] == position and edge1["relation_type"] == predicate:
            return True
    return False


#directory = "/home/scai/Workspace/hshi33/virtualHome/data/full_dataset/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2/"
directory = "full_dataset/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2"
with open(os.path.join(directory, "label_new.json"), "r") as label_file:
    label_data = json.load(label_file)
files = os.listdir(directory)
files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
print(len(files))
valid_files = []
dict = {}
count = 0

for file in files:
    try:
        if file == "label_new.json" or file == "question_types.json":
            continue
        file1 = open(os.path.join(directory, file), "rb")
        data = pickle.load(file1)
        if data["obs"] == []:
            continue
        goal_0 = data["goals"][0]
        goal_1 = data["goals"][1]
        dict[file] = []
        if data["fail_to_execute"] == True:
            continue
            dict[file].append("fail_to_execute")
        if len(label_data[file]) == 0:
            continue
        have_language = False
        for index, language in enumerate(data["language_object"][1]):
            if language is None:
                continue
            have_language = True
            if "intentional_help(language)" in label_data[file] or "intentional_hinder(language)" in label_data[file] or "failed_help" in label_data[file] or "failed_hinder" in label_data[file]:
                if language.try_to_hinder:
                    dict[file].append("1.a.ii.1")
                    dict[file].append("1.a.ii.2")
                    if "intentional_help(action)" in label_data[file]:
                        dict[file].append("3.b.ii")
                else:
                    dict[file].append("1.a.i.1")
                    dict[file].append("1.a.i.2")
                    if "intentional_hinder(action)" in label_data[file]:
                        dict[file].append("3.b.i")
                dict[file].append("2.a.i")
                dict[file].append("2.a.ii.1")
                dict[file].append("2.a.ii.2")
            break
        if not have_language:
            agent_0_goals = []
            for goal, info in goal_0.items():
                agent_0_goals.append(goal.split("_")[1])
            '''
            if "accidental_help" or "accidental_hinder" in label_data[file]:
                dict[file].append("2.b.i_independent")
                dict[file].append("2.b.ii_independent")
                dict[file].append("3.a.i_not_know")
            elif "intentional_hinder(action)" in label_data[file]:
                dict[file].append("2.b.i_hinder")
                dict[file].append("2.b.ii_hinder")
                dict[file].append("3.a.i_know")
            elif "intentional_help(action)" in label_data[file]:
                dict[file].append("2.b.i_help")
                dict[file].append("2.b.ii_help")
                dict[file].append("3.a.i_know")
            '''
            if "accidental_help" in label_data[file]:
                goal_align = True
                for goal, info in goal_1.items():
                    if goal.split("_")[1] not in agent_0_goals:
                        dict[file].append("2.b.i_independent")
                        dict[file].append("2.b.ii")
                        #dict[file].append("3.a.i_not_know")
                        goal_align = False
                        break
                if goal_align:
                    dict[file].append("2.b.i_help")
                    dict[file].append("2.b.ii")
                    #dict[file].append("3.a.i_know")
            elif "accidental_hinder" in label_data[file]:
                goal_align = True
                for goal, info in goal_1.items():
                    if goal.split("_")[1] not in agent_0_goals:
                        dict[file].append("2.b.i_independent")
                        dict[file].append("2.b.ii")
                        #dict[file].append("3.a.ii_not_know")
                        goal_align = False
                        break
                if goal_align:
                    dict[file].append("2.b.i_hinder")
                    dict[file].append("2.b.ii")
                    #dict[file].append("3.a.ii_know")
                
        print(dict[file])
    except Exception as e:
        print(str(e))
        continue
with open(os.path.join(directory, "question_types.json"), "w") as json_file:
    json.dump(dict, json_file, indent=4)



