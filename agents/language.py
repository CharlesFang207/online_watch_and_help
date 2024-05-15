import numpy as np
import random
from simulation.evolving_graph.utils import load_graph_dict, load_name_equivalence
from simulation.evolving_graph.environment import EnvironmentState, EnvironmentGraph, GraphNode
import scipy.special
import ipdb
import pdb
import sys
import simulation.evolving_graph.utils as vh_utils
import json
import copy
from termcolor import colored

class Language():
    def __init__(self, from_agent_id=None, to_agent_id=None, language_type=None):
        self.from_agent_id = from_agent_id
        self.to_agent_id = to_agent_id
        self.language_type = language_type


class LanguageInquiry(Language):
    def __init__(self, obj_name=None, from_agent_id=None, to_agent_id=None, language_type=None):
        super().__init__(from_agent_id, to_agent_id, language_type)
        self.obj_name = obj_name
    
    # Use the helper's belief and sampled graph to extract the most certain object information
    def extract_max_prob_obj_info(self, sampled_graph, edge_belief):
        assert(self.language_type == 'location')
        assert(self.obj_name is not None)
        
        obj_ids = [node["id"] for node in sampled_graph["nodes"] if node["class_name"] == self.obj_name]
        max_obj_id_prob = [None, 0.]
        pred = None
        position_id = None

        for obj_id in obj_ids:
            if obj_id not in edge_belief:
                continue
            else:
                max_inside_prob = max(scipy.special.softmax(edge_belief[obj_id]["INSIDE"][1][1:])) #TODO: do we need softmax
                max_on_prob = max(scipy.special.softmax(edge_belief[obj_id]["ON"][1][1:]))
                max_prob = max(max_inside_prob, max_on_prob)
                if (max_prob > max_obj_id_prob[1]):
                #TODO: decide whether to respond based on max_prob
                    if max_inside_prob == max_prob:
                        #use 1: because first element in the list is None, can add more logic in the future
                        index_list = np.argwhere(scipy.special.softmax(edge_belief[obj_id]["INSIDE"][1][1:]) == max_inside_prob).flatten()
                        index = np.random.choice(index_list)
                        container_id = edge_belief[obj_id]["INSIDE"][0][index]
                        '''try:
                            container_id = edge_belief[obj_id]["INSIDE"][0][index]
                        except TypeError:
                            ipdb.set_trace()'''
                        pred = "INSIDE"
                        position_id = container_id
                    else:
                        index_list = np.argwhere(scipy.special.softmax(edge_belief[obj_id]["ON"][1][1:]) == max_on_prob).flatten()
                        index = np.random.choice(index_list)
                        surface_id = edge_belief[obj_id]["ON"][0][index]
                        pred = "ON"
                        position_id = surface_id
                    max_obj_id_prob = [obj_id, max_prob]
        #TODO: if position_id is None:
        return pred, max_obj_id_prob[0], position_id
        


class LanguageResponse(Language):
    def __init__(self, pred, obj_name=None, obj_id=None, position_id=None, goal_spec=None, from_agent_id=None, to_agent_id=None, language_type=None):
        # obj_name is used for the natural language conversation. But actually we use obj_id implicitly to avoid ambiguity, we need the obj_id
        super().__init__(from_agent_id, to_agent_id, language_type)

        if language_type == 'location':
            assert(pred is not None and obj_name is not None and obj_id is not None and position_id is not None)
            self.language = '{}_{}_{}'.format(pred, obj_name, position_id)
            self.obj_id = obj_id
        elif language_type == 'goal':
            assert(goal_spec is not None)
            self.language = goal_spec.keys()[0] # xinyu: since we don't need multiple goals for an single agent,  I just choose the first one here
            self.goal_spec = goal_spec
            # raise NotImplementedError('Goal language not implemented yet') 
            
        else:
            raise ValueError('Language type not recognized')
        
    def parse(self):
        return self.language.split('_')
