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
    api_key=''
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
            if "room" in node["class_name"]:
                continue
            for edge in sampled_graph["edges"]:
                if edge["from_id"] == node["id"] and edge["relation_type"] == "INSIDE" and "room" in id2class[edge["to_id"]]:
                    id2room[node["id"]] = id2class[edge["to_id"]]
                    break
        '''print(id2class)
        print(id2room)'''
                
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
                        maxIndex = np.argmax(edge_belief[obj_id]["INSIDE"][1][:])
                        if hinder > 1/3: #not hindering
                            obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][maxIndex]})
                            if edge_belief[obj_id]["INSIDE"][0][maxIndex] is not None:
                                obj_position[obj_name][obj_id]["class_name"] = id2class[edge_belief[obj_id]["INSIDE"][0][maxIndex]]
                                obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["INSIDE"][0][maxIndex]]
                        else:
                            temp = []
                            for i in range(1, edge_belief[obj_id]["INSIDE"][1].shape[0]):
                                if i == maxIndex:
                                    continue
                                temp.append(edge_belief[obj_id]["INSIDE"][1][i])
                            index = random.choice(temp) #choose a random position
                            obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index], "class_name":id2class[obj_id]})
                            #if edge_belief[obj_id]["INSIDE"][0][index] is not None:
                            obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["INSIDE"][0][index]]
                    else:
                        entropy = -np.sum(distribution * np.log2(distribution))
                        ratio = entropy / np.log2(distribution.shape[0])
                        if ratio <= 0.5: #certain enough, for testing purpose have 1.0 now
                            if obj_id not in obj_position[obj_name].keys():
                                obj_position[obj_name][obj_id] = []
                            maxIndex = np.argmax(edge_belief[obj_id]["INSIDE"][1][:])
                            if hinder > 1/3:
                                obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][maxIndex]})
                                if edge_belief[obj_id]["INSIDE"][0][maxIndex] is not None:
                                    obj_position[obj_name][obj_id]["class_name"] = id2class[edge_belief[obj_id]["INSIDE"][0][maxIndex]]
                                    obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["INSIDE"][0][maxIndex]]
                            else:
                                temp = []
                                for i in range(1, edge_belief[obj_id]["INSIDE"][1].shape[0]):
                                    if i == maxIndex:
                                        continue
                                    temp.append(edge_belief[obj_id]["INSIDE"][1][i])
                                index = random.choice(temp) #choose a random position
                                obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index], "class_name":id2class[obj_id]})
                                #if edge_belief[obj_id]["INSIDE"][0][index] is not None:
                                obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["INSIDE"][0][index]]
                            '''for index, element in enumerate(distribution):
                                if element > 1 / distribution.shape[0]:
                                    obj_position[obj_name][obj_id].append({"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index]})'''
                    distribution = scipy.special.softmax(edge_belief[obj_id]["ON"][1][:])
                    distribution = distribution[distribution > 0]
                    if distribution.shape[0] == 1:
                        maxIndex = np.argmax(edge_belief[obj_id]["ON"][1][:])
                        if hinder > 1/3:
                            obj_position[obj_name][obj_id].append({"predicate": "on", "position": edge_belief[obj_id]["ON"][0][maxIndex]})
                            if edge_belief[obj_id]["ON"][0][maxIndex] is not None:
                                obj_position[obj_name][obj_id]["class_name"] = id2class[edge_belief[obj_id]["ON"][0][maxIndex]]
                                obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["ON"][0][maxIndex]]
                        else:
                            temp = []
                            for i in range(1, edge_belief[obj_id]["ON"][1].shape[0]):
                                if i == maxIndex:
                                    continue
                                temp.append(edge_belief[obj_id]["ON"][1][i])
                            index = random.choice(temp) #choose a random position
                            obj_position[obj_name][obj_id].append({"predicate": "on", "position": edge_belief[obj_id]["ON"][0][index], "class_name":id2class[obj_id]})
                            #if edge_belief[obj_id]["INSIDE"][0][index] is not None:
                            obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["ON"][0][index]]
                        continue
                    entropy = -np.sum(distribution * np.log2(distribution))
                    ratio = entropy / np.log2(distribution.shape[0])
                    if ratio <= 1.0: #certain enough, for testing purpose have 1.0 now
                        if obj_id not in obj_position[obj_name].keys():
                            obj_position[obj_name][obj_id] = []
                        maxIndex = np.argmax(edge_belief[obj_id]["ON"][1][:])
                        if hinder > 1/3:
                            obj_position[obj_name][obj_id].append({"predicate": "on", "position": edge_belief[obj_id]["ON"][0][maxIndex]})
                            if edge_belief[obj_id]["ON"][0][maxIndex] is not None:
                                obj_position[obj_name][obj_id]["class_name"] = id2class[edge_belief[obj_id]["ON"][0][maxIndex]]
                                obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["ON"][0][maxIndex]]
                        else:
                            temp = []
                            for i in range(1, edge_belief[obj_id]["ON"][1].shape[0]):
                                if i == maxIndex:
                                    continue
                                temp.append(edge_belief[obj_id]["ON"][1][i])
                            index = random.choice(temp) #choose a random position
                            obj_position[obj_name][obj_id].append({"predicate": "on", "position": edge_belief[obj_id]["ON"][0][index], "class_name":id2class[edge_belief[obj_id]["ON"][0][index]]})
                            #if edge_belief[obj_id]["INSIDE"][0][index] is not None:
                            obj_position[obj_name][obj_id]["room"] = id2room[edge_belief[obj_id]["ON"][0][index]]
        for obj_name in obj_position.keys():
            if len(obj_position[obj_name].keys()) == 0: #indicating that agent is unsure about the object
                if hinder < 1/3:
                    for obj_id in obj_ids[obj_name]:
                        distribution = edge_belief[obj_id]["INSIDE"][0] #choose inside because it will hinder more effectively
                        index = random.choice(range(1, distribution.shape[0]))
                        obj_position[obj_name][obj_id] = [{"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index], "class_name": id2class[edge_belief[obj_id]["INSIDE"][0][index]], "room": id2room[edge_belief[obj_id]["INSIDE"][0][index]]}]
                continue
            for obj_id in obj_position[obj_name].keys():
                if len(obj_position[obj_name][obj_id]) == 1 and obj_position[obj_name][obj_id][0]["position"] is None:
                    if hinder < 1/3:
                        distribution = edge_belief[obj_id]["INSIDE"][0] #choose inside because it will hinder more effectively
                        index = random.choice(range(1, distribution.shape[0]))
                        obj_position[obj_name][obj_id] = [{"predicate": "inside", "position": edge_belief[obj_id]["INSIDE"][0][index], "class_name": id2class[edge_belief[obj_id]["INSIDE"][0][index]], "room": id2room[edge_belief[obj_id]["INSIDE"][0][index]]}]
            
        return LanguageResponse(obj_position, from_agent_id=self.to_agent_id, to_agent_id=self.from_agent_id, language_type="location", try_to_hinder=(hinder < 1/3))


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
            model="gpt-4",
        )
        return response.choices[0].message.content.strip()
        


class LanguageResponse(Language):
    def __init__(self, obj_positions=None, goal_spec=None, from_agent_id=None, to_agent_id=None, language_type=None, try_to_hinder=False):
        # obj_name is used for the natural language conversation. But actually we use obj_id implicitly to avoid ambiguity, we need the obj_id
        super().__init__(from_agent_id, to_agent_id, language_type)
        if language_type == 'location':
            assert(obj_positions is not None)
            self.obj_positions = obj_positions
            self.try_to_hinder = try_to_hinder
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
                info = ""
                for obj_name in self.obj_positions.keys():
                    if len(self.obj_positions[obj_name].keys()) == 0:
                        info += "{} null; ".format(obj_name)
                    else:
                        for obj_id in self.obj_positions[obj_name].keys():
                            for location in self.obj_positions[obj_name][obj_id]:
                                if location["position"] is None:
                                    info += "{} null; ".format(obj_name)
                                else:
                                    info += "{} {} {} {} {}; ".format(obj_name, location["predicate"], location["position"], location["class_name"], location["room"])
                
                prompt2 = """
                        Generate natural language from language template.
                        The user will provide the locations of an object with a basic templated format, with entries seperated by ;.
                        Convert this statement into natural conversational language.
                        Be creative with the responses to make it seem like everyday conversation.
                        Here are some examples of how to respond:

                        User: plate on coffeetable 133 livingroom; juice inside fridge 231 kitchen
                        Response: I saw the plate on the coffee table in the living room, and the juice is inside the fridge in the kitchen.

                        User: waterglass on table 120 livingroom
                        Response: I found the water glass sitting on the table in the living room.

                        User: apple on table 121 livingroom; apple inside fridge 240 kitchen; apple on kitchencounter 301 kitchen
                        Response: I noticed an apple on the table in the living room, another inside the fridge in the kitchen, and one more on the kitchen counter.

                        If the user says "null", respond naturally with different forms of "I don't know".
                        If there are several repeating items, only respond once to that item.
                        Here are some examples:

                        User: plate null
                        Response: Sorry, I don't know where there plate is"

                        User: laptop null; chair on floor 100 livingroom
                        Response: I don't know where the laptop is, but I noticed the chair on the floor in the living room.

                        User: wine null; wine null
                        Response: I'm not sure where the wine is.

                        Now Complete this:

                        User: 
                        """

                prompt_end = "\nResponse: "
                prompt2 += info
                prompt2 += prompt_end

                response2 = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt2,
                        }
                    ],
                    model="gpt-4",
                )

                return response2.choices[0].message.content.strip()