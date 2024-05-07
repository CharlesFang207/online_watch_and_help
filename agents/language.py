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
    def __init__(self, obj_name, from_agent_id=None, to_agent_id=None):
        self.obj_name = obj_name
        self.from_agent_id = from_agent_id
        self.to_agent_id = to_agent_id


class LanguageInquiry(Language):
    def __init__(self, obj_name, from_agent_id=None, to_agent_id=None):
        super().__init__(obj_name, from_agent_id, to_agent_id)
    
    # Use the helper's belief and sampled graph to extract the most certain object information
    def extract_max_prob_obj_info(self, sampled_graph, edge_belief):
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
    def __init__(self, language_type, pred, obj_name, obj_id, position_id, from_agent_id=None, to_agent_id = None):
        # obj_name is used for the natural language conversation. But actually we use obj_id implicitly to avoid ambiguity, we need the obj_id
        super().__init__(obj_name, from_agent_id, to_agent_id)
        self.language_type = language_type

        if language_type == 'location':
            self.language = '{}_{}_{}'.format(pred, obj_name, position_id)
        elif language_type == 'goal':
            raise NotImplementedError('Goal language not implemented yet') 
            # TODO: Implement goal language.  SHould it be in the LanguageResponse class or LanguageInquiry class?
        else:
            raise ValueError('Language type not recognized')
        
    def parse(self):
        return self.language.split('_')
