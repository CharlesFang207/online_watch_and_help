import sys
import os
curr_dir = os.path.dirname(os.path.abspath(__file__))
home_path = "../../"
sys.path.insert(0, f"{curr_dir}/../../virtualhome/virtualhome/")
from simulation.unity_simulator import comm_unity
comm = comm_unity.UnityCommunication(
            port="8092",
            file_name="/home/scai/Workspace/hshi33/virtualhome/online_watch_and_help/path_sim_dev/linux_exec.v2.3.0.x86_64",
            no_graphics=True,
            logging=False,
            x_display=0,
            timeout_wait=60
        )
comm.reset(1)
temp = {'kitchentable': [199], 'coffeetable': [86, 289], 'sofa': [85, 288], 'bathroomcabinet': [26], 'kitchencabinet': [202, 203, 204, 205, 206, 207, 208, 209], 'cabinet': [87], 'fridge': [225], 'stove': [226], 'dishwasher': [228], 'microwave': [234]}
s, g = comm.environment_graph()
nodes = [{'id': 1000, 'class_name': 'bread'}]
         #{'id': 1002, 'class_name': 'plate'}, {'id': 1003, 'class_name': 'plate'}]
         #{'id': 1004, 'class_name': 'cutleryfork'}, {'id': 1005, 'class_name': 'cutleryfork'}]
edges = [{'from_id': 1000, 'relation_type': 'ON', 'to_id': 288}]
         #{'from_id': 1002, 'relation_type': 'INSIDE', 'to_id': 234}, {'from_id': 1003, 'relation_type': 'INSIDE', 'to_id': 311}]
         #{'from_id': 1004, 'relation_type': 'INSIDE', 'to_id': 235}, {'from_id': 1005, 'relation_type': 'INSIDE', 'to_id': 234}]
g["nodes"] += nodes
g["edges"] += edges
success, message = comm.expand_scene(
                        g, transfer_transform=False
                    )
print(success)
'''comm.add_character('Chars/Female2')
scripts = [
    '<char0> [walk] <cellphone> (330)',
    '<char0> [grab] <cellphone> (330)',
    '<char0> [walk] <bathroomcounter> (86)',
    '<char0> [putback] <cellphone> (330) <coffeetable> (86)'
]
for script in scripts:
    s, message = comm.render_script([script], recording=False, image_synthesis=[],
                        skip_animation=True)
    print(s, message)'''
s, g = comm.environment_graph()
for node in g["nodes"]:
    if node["class_name"] == "bread":
        print(node)
for edge in g["edges"]:
    if edge["from_id"] == 330 and edge["to_id"] == 288 and edge["relation_type"] == "ON":
        print("success")
        for node in g["nodes"]:
            if node["id"] == edge["from_id"]:
                print(node)