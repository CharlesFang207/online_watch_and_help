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
print("here")
comm.reset(0)
s, g = comm.environment_graph()
room_ids = [11, 73, 205, 335]
for edge in g["edges"]:
    if edge["to_id"] == 111 and edge["relation_type"] == "on":
        g["edges"].remove(edge)
        for node in g["nodes"]:
            if node["id"] == edge["from_id"]:
                g["nodes"].remove(node)
dict = {48: 'bathroomcabinet', 105: 'bookshelf', 234: 'kitchencabinet', 305: 'fridge', 311: 'stove', 313: 'microwave'}
import json
with open(f"{curr_dir}/data/object_info_final.json", "r") as file:
    obj_info = json.load(file)
node = {"id": 456, "class_name": "plate"}
edges = [{"from_id": 456, "to_id": 372, "relation_type": "on"}]
g["nodes"].append(node)
g["edges"] += edges
s, message = comm.expand_scene(g)
print(s, message)
'''id = 1000
temp = g["nodes"]
results = {}
for container_id in dict.keys():
    for k in obj_info.keys():
        id += 1
        node = {"id": id, "class_name": k}
        edge = {"from_id": id, "to_id": container_id, "relation_type": "inside"}
        g["nodes"].append(node)
        g["edges"].append(edge)
        s, message = comm.expand_scene(g, transfer_transform=False)
        if not s:
            if dict[container_id] not in results.keys():
                results[dict[container_id]] = [k]
            else:
                results[dict[container_id]].append(k)
        g["nodes"].remove(node)
        g["edges"].remove(edge)
print(results)'''
s, g = comm.environment_graph()
for node in g["nodes"]:
    if node["class_name"] == "wineglass":
        print(node)
