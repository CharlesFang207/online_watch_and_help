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
        )
comm.reset(0)
s, g = comm.environment_graph()
nodes = [{'id': 1000, 'class_name': 'wineglass'}, {'id': 1001, 'class_name': 'wineglass'}]
         #{'id': 1002, 'class_name': 'plate'}, {'id': 1003, 'class_name': 'plate'}]
         #{'id': 1004, 'class_name': 'cutleryfork'}, {'id': 1005, 'class_name': 'cutleryfork'}]
edges = [{'from_id': 1000, 'relation_type': 'INSIDE', 'to_id': 237}, {'from_id': 1001, 'relation_type': 'INSIDE', 'to_id': 236}]
         #{'from_id': 1002, 'relation_type': 'INSIDE', 'to_id': 234}, {'from_id': 1003, 'relation_type': 'INSIDE', 'to_id': 311}]
         #{'from_id': 1004, 'relation_type': 'INSIDE', 'to_id': 235}, {'from_id': 1005, 'relation_type': 'INSIDE', 'to_id': 234}]
g["nodes"] += nodes
g["edges"] += edges
success, message = comm.expand_scene(
                        g, transfer_transform=False
                    )
print(success)
node = {"id": 1003, "class_name": "plate"}
g["nodes"].append(node)
success, message = comm.expand_scene(
                        g, transfer_transform=False
                    )
print(success)
