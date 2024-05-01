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
class LanguageInquiry():
    def __init__(self, obj_name, from_agent_id=None, to_agent_id=None):
        self.obj_name = obj_name
        self.from_agent_id = from_agent_id
        self.to_agent_id = to_agent_id


class LanguageResponse():
    def __init__(self, language_type, pred, obj_name, position_id, from_agent_id=None, to_agent_id = None):
        self.language_type = language_type
        self.from_agent_id = from_agent_id
        self.to_agent_id = to_agent_id

        if language_type == 'location':
            self.language = '{}_{}_{}'.format(pred, obj_name, position_id)
        elif language_type == 'goal':
            raise NotImplementedError('Goal language not implemented yet') 
            # TODO: Implement goal language.  SHould it be in the LanguageResponse class or LanguageInquiry class?
        else:
            raise ValueError('Language type not recognized')
        
    def parse(self):
        return self.language.split('_')
