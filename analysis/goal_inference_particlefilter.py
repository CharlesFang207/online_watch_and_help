import sys

sys.path.append(".")
import shutil
import os
import logging
import traceback
import pickle as pkl
import random
from tqdm import tqdm
import pickle
import copy
from pathlib import Path
import numpy as np
import pdb
import ipdb
import hydra
import time
import multiprocessing as mp
from omegaconf import DictConfig, OmegaConf
from dataloader.dataloader_v2 import AgentTypeDataset
from dataloader import dataloader_v2 as dataloader_v2
from models import agent_pref_policy_task as agent_pref_policy
from hydra.utils import get_original_cwd, to_absolute_path
from utils import utils_models_wb, utils_rl_agent, utils_environment

from envs.unity_environment import UnityEnvironment
from agents import MCTS_agent, MCTS_agent_particle_v2_instance, MCTS_agent_particle

# from arguments import get_args
from algos.arena_mp2 import ArenaMP
from utils import utils_goals
from utils import utils_exception
import torch

info_objects = {
    "objects_inside": [
        "bathroomcabinet",
        "kitchencabinet",
        "cabinet",
        "fridge",
        "stove",
        "dishwasher",
        "microwave",
    ],
    "objects_surface": [
        "bench",
        "cabinet",
        "chair",
        "coffeetable",
        "desk",
        "kitchencounter",
        "kitchentable",
        "nightstand",
        "sofa",
    ],
    "objects_grab": [
        "apple",
        "book",
        "coffeepot",
        "cupcake",
        "cutleryfork",
        "juice",
        "pancake",
        "plate",
        "poundcake",
        "pudding",
        "remotecontrol",
        "waterglass",
        "whippedcream",
        "wine",
        "wineglass",
    ],
    "others": ["character"],
}

def compute_metrics(pred_graphs, task_graph_gt):
    eps = 1e-9
    pos_preds = np.array([0, 0, 0, 2, 0, 5, 0, 3, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0,
                          0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                          0, 0, 0, 0, 0, 0, 0, 2, 0, 7, 0, 2, 0, 0, 2, 0, 0, 0, 3, 7,
                          0, 0, 3, 0, 0, 0, 0, 0, 0, 3, 7, 0, 0, 3, 0, 0, 0, 0, 0, 0,
                          2, 0, 6, 0, 3, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
                          0, 0, 2, 0, 7, 0, 3, 0, 0, 2, 0, 0, 0, 2, 6, 0, 0, 3, 0, 0,
                          0, 0, 0, 0, 3, 6, 0, 0, 3, 0, 0, 0, 0, 0, 1, 1])
    pred_task = np.concatenate([pred_graph[None, ...] for pred_graph in pred_graphs])
    gt_task = task_graph_gt[None, ...]

    pos_gt_p = (gt_task > 0) / ((gt_task > 0).sum(-1)[..., None] + eps)
    pred_p = (pred_task > 0) / ((pred_task > 0).sum(-1)[..., None] + eps)
        

    accuracy = (((gt_task == pred_task) * pos_gt_p).sum(-1)).mean(0)[None, ...]
    recall = (np.minimum(pred_task, gt_task).sum(-1) / (eps+gt_task.sum(-1))).mean(0)[None, ...]
    prec = (np.minimum(pred_task, gt_task).sum(-1) / (eps+pred_task.sum(-1))).mean(0)[None, ...]
    
    accuracymax = (((gt_task == pred_task) * pos_gt_p).sum(-1)).max(0)[None, ...]
    recallmax = (np.minimum(pred_task, gt_task).sum(-1) / (eps+gt_task.sum(-1))).max(0)[None, ...]
    precmax = (np.minimum(pred_task, gt_task).sum(-1) / (eps+pred_task.sum(-1))).max(0)[None, ...]
    return {
	'recall': recall,
	'recallmax': recallmax,
	'accuracy': accuracy,
	'accuracymax': accuracymax,
	'precision': prec,
        'precisionmax': precmax
    
    }


class GoalInferenceParticle():
    def __init__(self, planner, prediction_net, args_pred, graph_helper, class2id, arena, num_particles=10, num_proc=0, z_vec=None):
        self.planner = planner
        self.prediction_net = prediction_net
        self.num_particles = num_particles
        self.arena = arena
        self.z_vec = z_vec

        self.particles = []
        self.num_proc = num_proc
        self.args_pred = args_pred
        self.graph_helper = graph_helper
        self.class2id = class2id
        self.num_steps_plan = 15

    def get_rejected_particles(self, current_action):
        index_reject = []
        current_action.replace('walktowards', 'walk')
        for index in range(self.num_particles):
            plan_particle = self.particles[index]['plan'][1]
            is_present = current_action in plan_particle
            if is_present:
                index_reject.append(index)
        return index_reject


    def get_pred_name(self, container_name):
        pred_name = "on"
        room_list = ["kitchen", "livingroom", "bedroom", "bathroom"]
        if container_name in info_objects["objects_inside"] or container_name in room_list:
            pred_name = "inside"
        return pred_name

    def get_edge_instance(self, pred, class2id, t, source="pred"):
        # pred_edge_prob = pred['edge_prob']
        # print(len(pred['edge_input'][t]), len(pred['edge_pred'][t]))

        t = min(t, len(pred) - 1)

        # Note: we will assume that all predicates should be achieved, some of the predicates
        # will be already correct, but this should make sure we don't undo tasks that
        # are already correct

        preds = pred[t][0]
        input_graph = pred[t][2]
        edge_pred_ins = {}
        # ipdb.set_trace()
        for predicate_name, count in preds.items():
            # print(cpred)
            # pred_name, count = cpred.split(':')
            obj_name, container_name = predicate_name
            obj_name, container_name = obj_name.strip(), container_name.strip()

            pred_name = self.get_pred_name(container_name)
            if obj_name == "character" or container_name in [
                "kitchen",
                "livingroom",
                "bedroom",
                "bathroom",
                "plate",
            ]:
                continue

            if obj_name in class2id:
                container_id = class2id[container_name][0]
                pred_name = f"{pred_name}_{obj_name}_{container_id}"
                edge_pred_ins[pred_name] = {
                    "count": count,
                    "grab_obj_ids": class2id[obj_name],
                    "container_ids": [container_id],
                }
            else:
                # Wrong prediction, this prediction did not exist
                pass
        # if len(edge_pred_ins) == 0:
        #     ipdb.set_trace()
        return edge_pred_ins

    def get_agent_plan(self, t, index_plan, res, obs, length_plan, 
                       must_replan, agent_id, current_goal):
        " Returns the plan of the agent"
        inferred_goal = self.get_edge_instance(current_goal, self.class2id, t)
        print("pred {}:".format(index_plan), inferred_goal)
        # ipdb.set_trace()
        plan_states, opponent_subgoal = None, None
        if len(inferred_goal) > 0:  # if no edge prediction then None action
            opponent_actions, opponent_info = self.planner(
                {0: obs},
                length_plan=length_plan,
                must_replan=must_replan,
                agent_id=agent_id,
                inferred_goal=inferred_goal,
            )
            plan_states = opponent_info[agent_id]["plan_states"]
            plan_cost = opponent_info[agent_id]["plan_cost"]
            plan = opponent_info[agent_id]["plan"]
            
            # ipdb.set_trace()
            if (
                opponent_info[agent_id]["subgoals"] is not None
                and len(opponent_info[agent_id]["subgoals"]) > 0
            ):
                opponent_subgoal = opponent_info[agent_id]["subgoals"][0][0]
            else:
                opponent_subgoal = None
            res[index_plan] = (opponent_subgoal, plan, plan_states, plan_cost)
        else:
            # This particle has not plan
            res[index_plan] = (None, [], [], 0.0)


    def plan_for_particles(self, curr_obs, particle_ids):
        num_goals = len(particle_ids)
        processes_used = min(len(particle_ids), self.num_proc)
        if processes_used == 0:
            res = {}
            t = 0
            for particle_id in particle_ids:
                self.get_agent_plan(
                    t,
                    particle_id,
                    res,
                    curr_obs,
                    self.num_steps_plan, # len_plan
                    {0: True, 1: True}, # must_replan
                    0, # agent_id
                    self.particles[particle_id]['pred_graph'],
                )
            
        else:
            t = 0
            # ipdb.set_trace()
            manager = mp.Manager()
            res = manager.dict()
            for start_root_id in range(0, num_goals, processes_used):
                end_root_id = min(
                    start_root_id + processes_used, num_goals
                )
                jobs = []
                for process_id in range(start_root_id, end_root_id):
                    # print(process_id)
                    particle_id = particle_ids[process_id]
                    p = mp.Process(
                        target=self.get_agent_plan,
                        args=(
                            t,
                            process_id,
                            res,
                            curr_obs,
                            self.num_steps_plan,
                            {0: True, 1: True},
                            0,
                            self.particles[particle_id]['pred_graph']
                        ),
                    )
                    jobs.append(p)
                    p.start()
                for p in jobs:
                    p.join()

        index = 0
        for particle_id in particle_ids:
            self.particles[particle_id]['plan'] = res[index]
            index += 1

    def regen_particles(self, graphs, observations, actions, particle_ids, t=None):
        history_graph = graphs
        history_obs = observations
        history_action = actions
        
        # if len(particle_ids) > 0:
        #     particle_ids = list(range(self.num_particles))
        inputs_func = (
            utils_models_wb.prepare_graph_for_task_model_diff(
                history_graph,
                history_obs,
                history_action,
                self.args_pred,
                self.graph_helper,
                batch_repeat=len(particle_ids)
        ))

        with torch.no_grad():
            if self.z_vec is not None:
                z_vec = self.z_vec.copy()
                z_vec[:len(particle_ids), :] = z_vec[particle_ids, :]
                output_func = self.prediction_net(inputs_func, inference=True, z_vec=torch.tensor(self.z_vec))
            else:
                output_func = self.prediction_net(inputs_func, inference=True)

        num_tsteps = output_func["pred_graph"].shape[1]
        pred_graph = output_func["pred_graph"].argmax(-1)
        
        # todo : get current plan?
        task_graph_input = self.graph_helper.get_task_graph(
                                inputs_func["input_task_graph"][0, 0], use_dict=True
                            )
        task_result = []
        # print(num_tsteps)
        for ind, index_particle in enumerate(particle_ids):
            task_graphs = []
            for tstep in [num_tsteps-1]:
                try:
                    curr_task_graph = self.graph_helper.get_task_graph(
                        pred_graph[ind, tstep], use_dict=True
                    )
                except:
                    print("Error processing graph")
                    ipdb.set_trace()
                # ipdb.set_trace()
                # curr_mask_task = mask_task_graph[ind, tstep]
                curr_mask_task = None
                task_graphs.append(
                    (
                        curr_task_graph,
                        curr_mask_task,
                        task_graph_input,
                        pred_graph[ind, tstep]
                    )
                )
            task_result.append(task_graphs)

            self.particles[index_particle]['pred_graph'] = task_graphs
        elem = []
        for i in range(self.num_particles):
            tg = self.particles[i]['pred_graph'][-1][-1]
            new_str = ''
            if i in particle_ids:
                new_str = '*'
            elem.append(new_str+str(int(tg.sum(-1))))
        print("time {}".format(t))
        print(' '.join(elem))
        # ipdb.set_trace()
        



    def initialize(self, graphs, observations, actions):
        self.arena.sim_agents[0].reset(observations[0], graphs[0], None, seed=0)
        history_graph = graphs
        history_obs = observations
        history_action = actions
        inputs_func = (
            utils_models_wb.prepare_graph_for_task_model_diff(
                history_graph,
                history_obs,
                history_action,
                self.args_pred,
                self.graph_helper,
                batch_repeat=self.num_particles
            ))

        with torch.no_grad():
            if self.z_vec is not None:
                output_func = self.prediction_net(inputs_func, inference=True, z_vec=torch.tensor(self.z_vec))
            else:
                output_func = self.prediction_net(inputs_func, inference=True)

        num_tsteps = output_func["pred_graph"].shape[1]
        pred_graph = output_func["pred_graph"].argmax(-1)
        
        # todo : get current plan?
        task_graph_input = self.graph_helper.get_task_graph(
                                inputs_func["input_task_graph"][0, 0], use_dict=True
                            )
        task_result = []
        for ind in range(self.num_particles):
            task_graphs = []
            for tstep in range(num_tsteps):
                try:
                    curr_task_graph = self.graph_helper.get_task_graph(
                        pred_graph[ind, tstep], use_dict=True
                    )
                except:
                    print("Error processing graph")
                    ipdb.set_trace()
                # ipdb.set_trace()
                # curr_mask_task = mask_task_graph[ind, tstep]
                curr_mask_task = None
                task_graphs.append(
                    (
                        curr_task_graph,
                        curr_mask_task,
                        task_graph_input,
                        pred_graph[ind, tstep]
                    )
                )
            task_result.append(task_graphs)
        self.particles = [{'pred_graph': task_res} for task_res in task_result]
        # ipdb.set_trace()
        all_particle_ids = [i for i in range(self.num_particles)]

        elem = []
        for i in range(self.num_particles):
            tg = self.particles[i]['pred_graph'][0][-1]
            new_str = ''
            
            elem.append(new_str+str(int(tg.sum(-1))))
        print(' '.join(elem))
        # ipdb.set_trace()

        # TODO: tianmin, this does not seem correct, but im not sure the logic of the func, can you check?
        obs = observations[-1]
        graph_obs = {
            'nodes': [node for node in graphs[-1]['nodes'] if node['id'] in obs],
            'edges': [edge for edge in graphs[-1]['edges'] if edge['from_id'] in obs and edge['to_id'] in obs],
               
        }
        self.plan_for_particles(graph_obs, all_particle_ids)

    def filter():
        pass

@hydra.main(config_path="../config/configs_for_help", config_name="config_diff_state")
def main(cfg: DictConfig):
    config = cfg
    print("Config")
    print(OmegaConf.to_yaml(cfg))
    args = config
    args_pred = args.agent_pred_graph
    num_proc = 20
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    # home_path = '../'
    rootdir = curr_dir + "/../"

    # args.dataset_path = f'{rootdir}/dataset/train_env_task_set_100_full.pik'
    # args.dataset_path = f'/data/vision/torralba/frames/data_acquisition/SyntheticStories/online_wah/agent_preferences/dataset/test_env_task_set_10_full.pik'
    args.dataset_path = f"/data/vision/torralba/frames/data_acquisition/SyntheticStories/online_wah/agent_preferences/dataset/structured_agent/test_env_task_set_60_full_task.all.pik"
    # args.dataset_path = './dataset/train_env_task_set_20_full_reduced_tasks_single.pik'

    valid_set_path = "/data/vision/torralba/frames/data_acquisition/SyntheticStories/online_wah/agent_preferences/analysis/test_set_reduced.txt"
    f = open(valid_set_path, "r")
    episode_ids = []
    filenames = []
    for filename in f:
        episode_ids.append(int(filename.split("episode.")[-1].split("_")[0]))
        filenames.append(filename)
    episode_ids = sorted(episode_ids)
    print(len(episode_ids))
    f.close()

    graph_helper = utils_rl_agent.GraphHelper(
        max_num_objects=args_pred["model"]["max_nodes"],
        toy_dataset=args_pred["model"]["reduced_graph"],
    )

    print(filenames[0])
    # ipdb.set_trace()
    with open(filenames[0].strip(), 'rb') as f:
        content = pkl.load(f)
    with open(filenames[0].strip().replace('.pik', '_reduced.pik'), 'rb') as f:
        content_reduced = pkl.load(f)

    with open('results_inference/VAE.KL.0.001/{}_result.pkl'.format(filenames[0].split('/')[-1].strip()), 'rb') as f:
        prev_infer = pkl.load(f)
        z_vec = prev_infer['z_vec']
    # ipdb.set_trace()
    steps_keep = utils_rl_agent.condense_walking(content['action'][0])
    # ipdb.set_trace()
    curr_graph = content['graph'][0]
    class2id = {}
    for node in curr_graph["nodes"]:
        if node["class_name"] not in class2id:
            class2id[node["class_name"]] = []
        class2id[node["class_name"]].append(node["id"])
    


    model = agent_pref_policy.GraphPredNetworkVAETask3(args_pred)
    state_dict = torch.load(args_pred.ckpt_load)["model"]

    state_dict_new = {}

    for param_name, param_value in state_dict.items():
        state_dict_new[param_name.replace("module.", "")] = param_value

    model.load_state_dict(state_dict_new)
    model.eval()
    agent_types = [
        ["full", 0, 0.05, False, 0, "uniform"],  # 0
        ["full", 0.5, 0.01, False, 0, "uniform"],  # 1
        ["full", -5, 0.05, False, 0, "uniform"],  # 2
        ["partial", 0, 0.05, False, 0, "uniform"],  # 3
        ["partial", 0, 0.05, False, 0, "spiked"],  # 4
        ["partial", 0, 0.05, False, 0.2, "uniform"],  # 5
        ["partial", 0, 0.01, False, 0.01, "spiked"],  # 6
        ["partial", -5, 0.05, False, 0.2, "uniform"],  # 7
        ["partial", 0.5, 0.05, False, 0.2, "uniform"],  # 8
    ]

    (
        args.obs_type,
        open_cost,
        walk_cost,
        should_close,
        forget_rate,
        belief_type,
    ) = agent_types[0]

    args_common = dict(
        recursive=False,
        max_episode_length=20,
        num_simulation=100,
        max_rollout_steps=5,
        c_init=0.1,
        c_base=100,
        num_samples=1,
        num_processes=num_proc,
        num_particles=20,
        logging=True,
        logging_graphs=True,
        get_plan_states=True,
        get_plan_cost=True,
    )
    agent_args = {
        "obs_type": args.obs_type,
        "open_cost": open_cost,
        "should_close": should_close,
        "walk_cost": walk_cost,
        "belief": {"forget_rate": forget_rate, "belief_type": belief_type},
    }

    args_agent1 = {"agent_id": 1, "char_index": 0}
    args_agent1.update(args_common)
    args_agent1["agent_params"] = agent_args
    agents = [
        lambda x, y: MCTS_agent_particle_v2_instance(**args_agent1),
    ]

    def env_fn(env_id):
        return UnityEnvironment(
            num_agents=1,
            max_episode_length=args.max_episode_length,
            port_id=env_id,
            env_task_set=None,
            observation_types=[args.obs_type, args.obs_type],
            use_editor=True,
            executable_args=None,
            base_port=args.base_port,
            convert_goal=True,
        )
    arena = ArenaMP(args.max_episode_length, 0, env_fn, agents, use_sim_agent=True)
    # ipdb.set_trace()
    particle_pred = GoalInferenceParticle(
        planner=arena.pred_actions, 
        prediction_net=model, 
        args_pred=args_pred, 
        graph_helper=graph_helper, 
        class2id=class2id, 
        arena=arena,
        num_particles=10, 
        num_proc=num_proc,
        z_vec=z_vec
    )


    graph_info, _ = graph_helper.build_graph_for_task(
            content['graph'][0], character_id=1,
            include_edges=True,
            obs_ids=content['obs'][0],
        unique_from=True
    )

    graph_info_end, _ = graph_helper.build_graph_for_task(
        content['graph'][-1], character_id=1,
        include_edges=True,
        obs_ids=content['obs'][-1],
        unique_from=True
    )

    task_graph_init = graph_helper.build_task_graph(graph_info)
    task_graph_end = graph_helper.build_task_graph(graph_info_end)
    task_graph_gt = np.maximum(task_graph_end - task_graph_init, np.zeros(task_graph_init.shape)) 

    curr_metrics = [] 
    curr_graphs = content['graph'][0]
    graphs = [utils_environment.inside_not_trans(curr_graph)]
    obs = [content['obs'][0]]
    actions = [None]
    particle_pred.z_vec = None
    particle_pred.initialize(graphs, obs, actions)
    pred_graphs = [particle['pred_graph'][-1][-1] for particle in particle_pred.particles]
    curr_metrics.append(compute_metrics(pred_graphs, task_graph_gt))
    t = 1
    cont_t_keep = 1
    for action in tqdm(content['action'][0]):
        if t in steps_keep:        
            curr_graphs = [content['graph'][0], content['graph'][t]]
            graphs = [utils_environment.inside_not_trans(utils_environment.clean_house_obj(graph)) for graph in curr_graphs]

            obs = [content['obs'][0], content['obs'][t]]
            actions = [None, None]

            rejected_particles =  particle_pred.get_rejected_particles(action)
            if len(rejected_particles):
                particle_pred.regen_particles(graphs, obs, actions, rejected_particles, cont_t_keep)
                filtered_graph_obs = {
                        'nodes': [node for node in graphs[-1]['nodes'] if node['id'] in obs[-1]],
                        'edges': [edge for edge in graphs[-1]['edges'] if edge['from_id'] in obs[-1] and edge['to_id'] in obs[-1]]
                }
                # ipdb.set_trace()

                
                particle_pred.arena.sim_agents[0].reset(filtered_graph_obs, graphs[-1], None, seed=0)
                particle_pred.plan_for_particles(filtered_graph_obs, rejected_particles)
            
            pred_graphs = [particle['pred_graph'][-1][-1] for particle in particle_pred.particles]
            curr_metrics.append(compute_metrics(pred_graphs, task_graph_gt))
            cont_t_keep += 1

        t += 1









    curr_metrics2 = [] 
    curr_graphs = content['graph'][0]
    graphs = [utils_environment.inside_not_trans(curr_graph)]
    obs = [content['obs'][0]]
    actions = [None]

    particle_pred.z_vec = z_vec
    particle_pred.initialize(graphs, obs, actions)
    pred_graphs = [particle['pred_graph'][-1][-1] for particle in particle_pred.particles]
    curr_metrics2.append(compute_metrics(pred_graphs, task_graph_gt))
    t = 1
    cont_t_keep = 0
    for action in tqdm(content['action'][0]):
        if t in steps_keep:

            curr_graphs = [content['graph'][0], content['graph'][t]]
            graphs = [utils_environment.inside_not_trans(utils_environment.clean_house_obj(graph)) for graph in curr_graphs]
            
            obs = [content['obs'][0], content['obs'][t]]
            actions = [None, None]


            rejected_particles = range(particle_pred.num_particles)
            if len(rejected_particles):
                particle_pred.regen_particles(graphs, obs, actions, rejected_particles)
                filtered_graph_obs = {
                        'nodes': [node for node in graphs[0]['nodes'] if node['id'] in obs[0]],
                        'edges': [edge for edge in graphs[0]['edges'] if edge['from_id'] in obs[0] and edge['to_id'] in obs[0]]
                }
                # ipdb.set_trace()
                graphc = filtered_graph_obs
                
                # particle_pred.arena.sim_agents[0].reset(filtered_graph_obs, graphs[0], None, seed=0)
                # particle_pred.plan_for_particles(filtered_graph_obs, rejected_particles)
            
            pred_graphs = [particle['pred_graph'][-1][-1] for particle in particle_pred.particles]
            curr_metrics2.append(compute_metrics(pred_graphs, task_graph_gt))

        t += 1

    # aggregate metrics
    final_metric_dict = {}
    for metric_name in curr_metrics[0].keys():
        final_metric_dict[metric_name] = np.array([metric[metric_name].item() for metric in curr_metrics])

    all_content = {}
    final_metric_dict2 = {}
    for metric_name in curr_metrics2[0].keys():
        final_metric_dict2[metric_name] = np.array([metric[metric_name].item() for metric in curr_metrics2])
    
    all_content['smart_reset'] = final_metric_dict
    all_content['all_reset'] = final_metric_dict2

    with open('result_inference.pkl', 'wb+') as f:
        pkl.dump(all_content, f)
    ipdb.set_trace()


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("running time: %s sec" % (time.time() - start_time))
