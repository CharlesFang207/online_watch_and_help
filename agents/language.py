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
from openai import OpenAI

client = OpenAI(
    api_key='sk-my-service-account-23HSd0AbqFBhw6h0fLt9T3BlbkFJ2j143nRn2ai1HplQxn4y'
)

class Language():
    def __init__(self, from_agent_id=None, to_agent_id=None, language_type=None):
        self.from_agent_id = from_agent_id
        self.to_agent_id = to_agent_id
        self.language_type = language_type


class LanguageInquiry(Language):
    def __init__(self, obj_list=None, from_agent_id=None, to_agent_id=None, language_type=None):
        super().__init__(from_agent_id, to_agent_id, language_type)
        self.obj_list = obj_list #name
    
    # Use the helper's belief and sampled graph to extract the most certain object information
    def generate_response(self, sampled_graph, edge_belief):
        assert(self.language_type == 'location')
        assert(self.obj_list is not None)
        hinder = random.random
        obj_ids = {} #map from object name to ids belong to that class
        for obj in self.obj_list:
            obj_ids[obj] = [node["id"] for node in sampled_graph["nodes"] if node["class_name"] == obj]
        
        '''max_obj_id_prob = [None, 0.]
        pred = None
        position_id = None'''

        #ipdb.set_trace()
        id2class = {}
        id2room = {}
        for node in sampled_graph["nodes"]:
            id2class[node["id"]] = node["class_name"]
        for node in sampled_graph["nodes"]:
            for edge in sampled_graph["edges"]:
                if edge["from_id"] == node["id"] and edge["relation_type"] == "INSIDE" and "room" in id2class[edge["to_id"]]:
                    id2room[node["id"]] = id2class[edge["to_id"]]
                    break
                
        obj_position = {}
        for obj_name in obj_ids.keys():
            obj_position[obj_name] = {}
            for obj_id in obj_ids[obj_name]:
                if obj_id not in edge_belief:
                    continue
                else:
                    distribution = scipy.special.softmax(edge_belief[obj_id]["INSIDE"][1][:])
                    distribution = distribution[distribution > 0] #filter out all zero probabilities
                    if distribution.shape[0] == 1: #case when belief is certain
                        #ipdb.set_trace()
                        obj_position[obj_name][obj_id] = []
                        index = np.argmax(edge_belief[obj_id]["INSIDE"][1][:])
                        if random.random() > 1/3: #2/3chance, not hindering
                        obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index], "class_name":id2class[obj_id], "room": id2room[obj_id]})
                    else:
                        entropy = -np.sum(distribution * np.log2(distribution))
                        ratio = entropy / np.log2(distribution.shape[0])
                        if ratio <= 0.5: #certain enough, for testing purpose have 1.0 now
                            if obj_id not in obj_position[obj_name].keys():
                                obj_position[obj_name][obj_id] = []
                            maxIndex = np.argmax(edge_belief[obj_id]["INSIDE"][1][:])
                            obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][maxIndex], "class_name":id2class[obj_id],  "room": id2room[obj_id]})
                            '''for index, element in enumerate(distribution):
                                if element > 1 / distribution.shape[0]:
                                    obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index]})'''
                    distribution = scipy.special.softmax(edge_belief[obj_id]["ON"][1][:])
                    distribution = distribution[distribution > 0]
                    if distribution.shape[0] == 1:
                        index = np.argmax(edge_belief[obj_id]["ON"][1][:])
                        obj_position[obj_name][obj_id].append({"predicate": "on", "position": edge_belief[obj_id]["ON"][0][maxIndex], "class_name":id2class[obj_id], "room": id2room[obj_id]})
                        continue
                    entropy = -np.sum(distribution * np.log2(distribution))
                    ratio = entropy / np.log2(distribution.shape[0])
                    if ratio <= 1.0: #certain enough, for testing purpose have 1.0 now
                        if obj_id not in obj_position[obj_name].keys():
                            obj_position[obj_name][obj_id] = []
                        maxIndex = np.argmax(edge_belief[obj_id]["ON"][1][:])
                        obj_position[obj_name][obj_id].append({"predicate": "on", "position": edge_belief[obj_id]["ON"][0][maxIndex], "class_name":id2class[obj_id], "room": id2room[obj_id]})
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
        prompt = """
                Generate natural language from a language template.
                The user will provide a question with a basic templated format.
                Convert this question into natural conversational language.
                Be creative with the responses to make it seem like everyday conversation.
                Here are some examples of how to respond:

                User: Where is wine?
                Response: Do you know where the wine is?

                User: Where is cup?
                Response: Have you seen a cup anywhere?

                User: Where is spoon? Where is plate?
                Response: Have you come across a spoon and a plate by any chance?

                Now complete this:

                User: 
                """
        
        question = ""
        for obj in self.obj_list:
            question += "Where is {}? ".format(obj)

        prompt_end = "\nResponse: "
        prompt += question
        prompt += prompt_end

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo",
        )
        return response.choices[0].message.content.strip()
        


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
    
    def to_language(self, mode="natural"):  # interface for converting to natural language
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
                                if location["position"] is None:
                                    #ans += "not {} anything".format(location["predicate"])
                                    continue
                                ans += " {} {}".format(location["predicate"], location["position"], location["class_name"], location["room"])
                            ans += "\n"
                return ans
            if mode == "natural": # natural communication
                return ""