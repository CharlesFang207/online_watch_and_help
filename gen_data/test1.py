import sys
import os
curr_dir = os.path.dirname(os.path.abspath(__file__))
home_path = "../../"
sys.path.insert(0, f"{curr_dir}/../../virtualhome/virtualhome/")
from simulation.unity_simulator import comm_unity
comm = comm_unity.UnityCommunication(
            port="8080",
            file_name="/home/scai/Workspace/hshi33/virtualhome/online_watch_and_help/path_sim_dev/linux_exec.v2.3.0.x86_64",
            no_graphics=True,
            logging=False,
            x_display=0,
)
surface_classes = [
            'kitchentable',
            'coffeetable',
            'sofa',
            'desk',
            'kitchencounter',
            'bathroomcounter'
        ]
container_classes = [
        'bathroomcabinet',
        'kitchencabinet',
        'cabinet',
        'fridge',
        'stove',
        'dishwasher',
        'microwave']
comm.reset(1)
s, g = comm.environment_graph()
object2ids = {}
for obj in surface_classes:
    object2ids[obj] = []
for obj in container_classes:
    object2ids[obj] = []
for node in g["nodes"]:
    if node["class_name"] in surface_classes or node["class_name"] in container_classes:
        object2ids[node["class_name"]].append(node["id"])
print(object2ids)
'''room_ids = [11, 73, 205, 335]
for edge in g["edges"]:
    if edge["to_id"] == 111 and edge["relation_type"] == "on":
        g["edges"].remove(edge)
        for node in g["nodes"]:
            if node["id"] == edge["from_id"]:
                g["nodes"].remove(node)
dict = {48: 'bathroomcabinet', 105: 'bookshelf', 234: 'kitchencabinet', 305: 'fridge', 311: 'stove', 313: 'microwave'}
'''
import json
import copy
import random
with open(f"{curr_dir}/data/real_object_placing.json", "r") as file:
    obj_info = json.load(file)
temp = copy.deepcopy(g)
new_graph = copy.deepcopy(temp)
result = {}
for obj, places in obj_info.items():
    if "food" in obj and obj != "food_food":
        obj = obj[5:]
    result[obj] = []
    designated_places = []
    for place in places:
        final = place["destination"].replace("_", "")
        #final = place[1].replace("_", "")
        designated_places.append(final)
    node = {"id": 1001, "class_name": obj}
    for container in container_classes:
        if container not in designated_places:
            continue
        dest_id = random.choice(object2ids[container])
        newgraph = copy.deepcopy(temp)
        edge = {"from_id":1001, "to_id": dest_id, "relation_type": "INSIDE"}
        newgraph["nodes"].append(node)
        newgraph["edges"].append(edge)
        s, message = comm.expand_scene(newgraph, transfer_transform=False)
        if s:
            result[obj].append(["INSIDE", container])
    for surface in surface_classes:
        if surface not in designated_places:
            continue
        dest_id = random.choice(object2ids[surface])
        newgraph = copy.deepcopy(temp)
        edge = {"from_id":1001, "to_id": dest_id, "relation_type": "ON"}
        newgraph["nodes"].append(node)
        newgraph["edges"].append(edge)
        s, message = comm.expand_scene(newgraph, transfer_transform=False)
        if s:
            result[obj].append(["ON", surface])
    if len(result[obj]) == 0:
        del(result[obj])
with open('object_info_new.json', 'w') as json_file:
    json.dump(result, json_file, indent=4)
