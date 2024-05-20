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
    def __init__(self, obj_list=None, from_agent_id=None, to_agent_id=None, language_type=None):
        super().__init__(from_agent_id, to_agent_id, language_type)
        self.obj_list = obj_list
    
    # Use the helper's belief and sampled graph to extract the most certain object information
    def generate_response(self, sampled_graph, edge_belief):
        assert(self.language_type == 'location')
        assert(self.obj_list is not None)
        
        obj_ids = {}
        for obj in self.obj_list:
            obj_ids[obj] = [node["id"] for node in sampled_graph["nodes"] if node["class_name"] == obj]
        
        '''max_obj_id_prob = [None, 0.]
        pred = None
        position_id = None'''

        obj_position = {}
        for obj_name in obj_ids.keys():
            obj_position[obj_name] = {}
            for obj_id in obj_ids[obj_name]:
                if obj_id not in edge_belief:
                    continue
                else:
                    combined = np.concatenate(edge_belief[obj_id]["INSIDE"][1][:], edge_belief[obj_id]["ON"][1][:])
                    distribution = scipy.special.softmax(combined)
                    entropy = -np.sum(distribution * np.log2(distribution))
                    ratio = entropy / np.log2(distribution.shape[0])
                    if ratio < 0.5: #certain enough
                        obj_position[obj_name][obj_id] = []
                        for index, element in enumerate(distribution):
                            if element > 1 / distribution.shape[0]:
                                if (index >= edge_belief[obj_id]["INSIDE"][1][:].shape[0]): # on something
                                    obj_position[obj_name][obj_id].append({"predicate": "on", "position": edge_belief[obj_id]["ON"][0][index - edge_belief[obj_id]["INSIDE"][1][:].shape[0]]})
                                else:
                                    obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index]})
        for obj_name in obj_position.keys():
            if len(obj_position[obj_name].keys()) == 0: #indicating that agent is unsure about the object
                pass #TODO: add logic related to situation when agent being asked is uncertain, by default it will answer I don't know
        return LanguageResponse(obj_position, from_agent_id=self.to_agent_id, to_agent_id=self.from_agent_id, language_type="location")


        '''            max_inside_prob = max(scipy.special.softmax(edge_belief[obj_id]["INSIDE"][1][1:])) #TODO: do we need softmax
                    max_on_prob = max(scipy.special.softmax(edge_belief[obj_id]["ON"][1][1:]))
                    max_prob = max(max_inside_prob, max_on_prob)
                    if (max_prob > max_obj_id_prob[1]):
                        


                    #TODO: decide whether to respond based on max_prob
                        if max_inside_prob == max_prob:
                            #use 1: because first element in the list is None, can add more logic in the future
                            index_list = np.argwhere(scipy.special.softmax(edge_belief[obj_id]["INSIDE"][1][1:]) == max_inside_prob).flatten()
                            index = np.random.choice(index_list)
                            container_id = edge_belief[obj_id]["INSIDE"][0][index]
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
        return pred, max_obj_id_prob[0], position_id'''
    
    def to_language(self):
        ans = ""
        for obj in self.obj_list:
            ans += "Where is {}?\n".format(obj)
        return ans
        


class LanguageResponse(Language):
    def __init__(self, obj_positions=None, goal_spec=None, from_agent_id=None, to_agent_id=None, language_type=None):
        # obj_name is used for the natural language conversation. But actually we use obj_id implicitly to avoid ambiguity, we need the obj_id
        super().__init__(from_agent_id, to_agent_id, language_type)

        if language_type == 'location':
            assert(obj_positions is not None)
            self.obj_positions = obj_positions
        elif language_type == 'goal':
            assert(goal_spec is not None)
            self.language = goal_spec.keys()[0] # xinyu: since we don't need multiple goals for an single agent,  I just choose the first one here
            self.goal_spec = goal_spec
            # raise NotImplementedError('Goal language not implemented yet') 
            
        else:
            raise ValueError('Language type not recognized')
        
    def parse(self):
        return self.language.split('_')
    
    def to_language(self, mode="full"):  # interface for converting to natural language
        if self.language_type == "location":
            ans = ""
            if mode == "full":  # all the information of communication, only for testing stage
                for obj_name in self.obj_positions.keys():
                    if len(self.obj_positions[obj_name].keys()) == 0:
                        ans += 'I do not know position of object {}.\n'.format(obj_name)
                    else:
                        ans += "Location of {}:\n".format(obj_name)
                        for obj_id in self.obj_positions[obj_name].keys():
                            ans += "{} {} ".format(obj_name, obj_id)
                            for location in self.obj_positions[obj_name][obj_id]:
                                ans += " {} {}".format(location["predicate"], location["position"])
                            ans += "\n"
                return ans
            if mode == "natural": # natural communication
                return ""