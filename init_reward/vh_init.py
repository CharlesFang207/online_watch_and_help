import pickle
import pdb
import sys
import os
import random
import json


random.seed(10)

home_path = '../../'
sys.path.append(home_path+'/vh_mdp')
sys.path.append(home_path+'/virtualhome')

from simulation.unity_simulator import comm_unity as comm_unity

from simulation.evolving_graph.utils import load_graph_dict
from profilehooks import profile


with open('object_info.json', 'r') as f:
    obj_position = json.load(f)

def remove_obj(graph, obj_ids):
    graph['nodes'] = [node for node in graph['nodes'] if node['id'] not in obj_ids]
    graph['edges'] = [edge for edge in graph['edges'] if edge['from_id'] not in obj_ids and edge['to_id'] not in obj_ids]
    
def add_obj(graph, obj_name, num_obj, object_id, obj_position_pool, only_position=None, except_position=None):
    if isinstance(except_position, int):
        except_position = [except_position]
    if isinstance(only_position, list):
        only_position = [only_position]

    edges = []
    nodes = []
    ids_class = {}
    for node in graph['nodes']:
        class_name = node['class_name']
        if class_name not in ids_class: ids_class[class_name] = []
        ids_class[class_name].append(node['id'])

    # TODO: we will want candidates per object later
    candidates = [('ON', obj_name) for obj_name in obj_position_pool['objects_surface'] if obj_name in ids_class.keys() and (except_position is None or obj_name not in except_position) and (only_position is None or obj_name in only_position)]
    candidates += [('INSIDE', obj_name) for obj_name in obj_position_pool['objects_inside'] if obj_name in ids_class and (except_position is None or obj_name not in except_position) and (only_position is None or obj_name in only_position)]
    for i in range(num_obj):
        # TODO: we need to check the properties and states, probably the easiest is to get them from the original set of graphs
        new_node = {'id': object_id, 'class_name': obj_name, 'properties': ['GRABBABLE'], 'states': [], 'category': 'added_object'}
        nodes.append(new_node)
        relation, target_classname = random.choice(candidates)
        target_id = random.choice(ids_class[target_classname])
        edges.append({'from_id': object_id, 'relation_type': relation, 'to_id': target_id})
        object_id += 1

    graph['nodes'] += nodes
    graph['edges'] += edges
    return object_id


def setup_other_objs(graph, object_id, num_obj=30, object_pool=obj_position):
    for i in range(num_obj):
        obj_name = random.choice(object_pool['objects_grab'])
        object_id = add_obj(graph, obj_name, 1, object_id, object_pool, only_position=None, except_position=None)
    return object_id

def set_tv_off(graph, tv_id):
    node = [n for n in graph['nodes'] if n['id'] == tv_id]
    node['states'] = 'OFF' + [state for state in node['states'] if node['states'] not in ['ON', 'OFF']]


class SetInitialGoal:
    def __init__(self, goal, obj_position, init_pool):
        self.goal = goal
        self.obj_position = obj_position
        self.init_pool = init_pool
        self.object_id_count = 1000

    def setup_table(self, graph, start=True):
        ## setup table
        # max_num_table = 4
        # num_table = random.randint(1, max_num_table)

        # table_ids = [node['id'] for node in graph['nodes'] if 'table' in node['class_name']]
        # remove_obj(graph, table_ids)
        # table_position_pool = self.obj_position['table']
        # add_obj(graph, 'table', num_table, table_position_pool)

        table_ids = [node['id'] for node in graph['nodes'] if 'table' in node['class_name']]
        table_id = random.choice(table_ids)

        for k,v in self.goal.items():
            obj_ids = [node['id'] for node in graph['nodes'] if k in node['class_name']]
            remove_obj(graph, obj_ids)

            num_obj = random.randint(v, self.init_pool[k]) # random select objects >= goal
            self.object_id_count = add_obj(graph, k, num_obj, self.object_id_count, self.obj_position, except_position=table_id)

        
        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)


        ## get goal
        env_goal = {'setup_table': []}
        for k,v in self.goal.items():
            env_goal['setup_table'].append( {'on_{}_{}'.format(k, table_id): v} )
        return graph, env_goal






    def clean_table(self, graph, start=True):
        ## clean table
        # max_num_table = 4
        # num_table = random.randint(1, max_num_table)

        # table_ids = [node['id'] for node in graph['nodes'] if 'table' in node['class_name']]
        # remove_obj(graph, table_ids)
        # table_position_pool = self.obj_position['table']
        # add_obj(graph, 'table', num_table, table_position_pool)
        

        table_ids = [node['id'] for node in graph['nodes'] if 'table' in node['class_name']]
        table_id = random.choice(table_ids)

        for k,v in self.goal.items():
            obj_ids = [node['id'] for node in graph['nodes'] if k in node['class_name']]
            remove_obj(graph, obj_ids)

            num_obj = random.randint(v, self.init_pool[k]) # random select objects >= goal
            self.object_id_count = add_obj(graph, k, v, self.object_id_count, self.obj_position, only_position=table_id) ## add the first v objects on this table
            self.object_id_count = add_obj(graph, k, num_obj-v, self.object_id_count, self.obj_position, except_position=table_id) ## add the rest objects on other places
        
        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)


        ## get goal
        env_goal = {'clean_table': []}
        for k,v in self.goal.items():
            env_goal['clean_table'].append( {'off_{}_{}'.format(k, table_id): v} )
        return graph, env_goal


    def put_diswasher(self, graph, start=True):
        ## setup diswasher
        # max_num_diswasher = 4
        # num_diswasher = random.randint(1, max_num_diswasher)

        # diswasher_ids = [node['id'] for node in graph['nodes'] if 'diswasher' in node['class_name']]
        # remove_obj(graph, diswasher_ids)
        # diswasher_position_pool = self.obj_position['diswasher']
        # add_obj(graph, 'diswasher', num_diswasher, diswasher_position_pool)
        

        diswasher_ids = [node['id'] for node in graph['nodes'] if 'diswasher' in node['class_name']]
        diswasher_id = random.choice(diswasher_ids)

        for k,v in self.goal.items():
            obj_ids = [node['id'] for node in graph['nodes'] if k in node['class_name']]
            remove_obj(graph, obj_ids)

            num_obj = random.randint(v, self.init_pool[k]) # random select objects >= goal
            self.object_id_count = add_obj(graph, k, num_obj, self.object_id_count, self.obj_position, except_position=diswasher_id)
        
        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)


        ## get goal
        env_goal = {'put_diswasher': []}
        for k,v in self.goal.items():
            env_goal['put_diswasher'].append( {'inside_{}_{}'.format(k, diswasher_id): v} )
        return graph, env_goal






    def unload_diswasher(self, graph, start=True):
        ## setup diswasher
        # max_num_diswasher = 4
        # num_diswasher = random.randint(1, max_num_diswasher)

        # diswasher_ids = [node['id'] for node in graph['nodes'] if 'diswasher' in node['class_name']]
        # remove_obj(graph, diswasher_ids)
        # diswasher_position_pool = self.obj_position['diswasher']
        # add_obj(graph, 'diswasher', num_diswasher, diswasher_position_pool)
        

        diswasher_ids = [node['id'] for node in graph['nodes'] if 'diswasher' in node['class_name']]
        diswasher_id = random.choice(diswasher_ids)


        for k,v in self.goal.items():
            obj_ids = [node['id'] for node in graph['nodes'] if k in node['class_name']]
            remove_obj(graph, obj_ids)

            num_obj = random.randint(v, self.init_pool[k]) # random select objects >= goal
            self.object_id_count = add_obj(graph, k, v, self.object_id_count, self.obj_position, only_position=diswasher_id) ## add the first v objects on this table
            self.object_id_count = add_obj(graph, k, num_obj-v, self.object_id_count, self.obj_position, except_position=diswasher_id) ## add the rest objects on other places
        
        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)


        ## get goal
        env_goal = {'unload_diswasher': []}
        for k,v in self.goal.items():
            env_goal['unload_diswasher'].append( {'off_{}_{}'.format(k, diswasher_id): v} )
        return graph, env_goal



    def put_fridge(self, graph, start=True):
        ## setup fridge
        # max_num_fridge = 4
        # num_fridge = random.randint(1, max_num_fridge)

        # fridge_ids = [node['id'] for node in graph['nodes'] if 'fridge' in node['class_name']]
        # remove_obj(graph, fridge_ids)
        # fridge_position_pool = self.obj_position['fridge']
        # add_obj(graph, 'fridge', num_fridge, fridge_position_pool)
        

        fridge_ids = [node['id'] for node in graph['nodes'] if 'fridge' in node['class_name']]
        fridge_id = random.choice(fridge_ids)

        for k,v in self.goal.items():
            obj_ids = [node['id'] for node in graph['nodes'] if k in node['class_name']]
            remove_obj(graph, obj_ids)

            num_obj = random.randint(v, self.init_pool[k]) # random select objects >= goal
            self.object_id_count = add_obj(graph, k, num_obj, self.object_id_count, self.obj_position, except_position=fridge_id)
        
        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)


        ## get goal
        env_goal = {'put_fridge': []}
        for k,v in self.goal.items():
            env_goal['put_fridge'].append( {'on_{}_{}'.format(k, fridge): v} )
        return graph, env_goal



    def read_book(self, graph, start=True):
        max_num_book = self.init_pool['book']
        num_book = random.randint(1, max_num_book)

        book_ids = [node['id'] for node in graph['nodes'] if 'book' in node['class_name']]
        remove_obj(graph, book_ids)
        self.object_id_count = add_obj(graph, 'book', num_table, self.obj_position)
        

        book_ids = [node['id'] for node in graph['nodes'] if 'book' in node['class_name']]
        book_id = random.choice(book_ids)

        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)

        ## get goal
        env_goal = {'read_book': [{'read_{}'.format(book_id)}]}
        return graph, env_goal


    def prepare_food(self, graph, start=True):
        # max_num_table = 4
        # num_table = random.randint(1, max_num_table)

        # table_ids = [node['id'] for node in graph['nodes'] if 'table' in node['class_name']]
        # remove_obj(graph, table_ids)
        # table_position_pool = self.obj_position['table']
        # add_obj(graph, 'table', num_table, table_position_pool)
        

        table_ids = [node['id'] for node in graph['nodes'] if 'table' in node['class_name']]
        table_id = random.choice(table_ids)


        for k,v in self.goal.items():
            obj_ids = [node['id'] for node in graph['nodes'] if k in node['class_name']]
            remove_obj(graph, obj_ids)

            num_obj = random.randint(v, self.init_pool[k]) # random select objects >= goal
            self.object_id_count = add_obj(graph, k, num_obj, self.obj_position, except_position=table_id)
        
        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)


        ## get goal
        env_goal = {'prepare_food': []}
        for k,v in self.goal.items():
            env_goal['prepare_food'].append( {'on_{}_{}'.format(k, table_id): v} )
        return graph, env_goal


    def watch_tv(self, graph, start=True):
        # max_num_tv = 4
        # num_tv = random.randint(1, max_num_tv)

        # tv_ids = [node['id'] for node in graph['nodes'] if 'tv' in node['class_name']]
        # remove_obj(graph, tv_ids)
        # tv_position_pool = self.obj_position['tv']
        # add_obj(graph, 'tv', num_tv, tv_position_pool)
        

        tv_ids = [node['id'] for node in graph['nodes'] if 'tv' in node['class_name']]
        tv_id = random.choice(tv_ids)

        set_tv_off(tv_id)

        if start:
            self.object_id_count = setup_other_objs(graph, self.object_id_count)

        ## get goal
        env_goal = {'watch_tv': [{'{}_on'.format(tv_id)}]}
        return graph, env_goal


    def setup_table_prepare_food(self, graph):
        graph, env_goal1 = self.setup_table(graph)
        graph, env_goal2 = self.prepare_food(graph, start=False)
        return graph, env_goal1.update(env_goal2)

    def setup_table_read_book(self, graph):
        graph, env_goal1 = self.setup_table(graph)
        graph, env_goal2 = self.read_book(graph, start=False)
        return graph, env_goal1.update(env_goal2)
    
    def setup_table_watch_tv(self, graph):
        graph, env_goal1 = self.setup_table(graph)
        graph, env_goal2 = self.watch_tv(graph, start=False)
        return graph, env_goal1.update(env_goal2)

    def setup_table_put_fridge(self, graph):
        graph, env_goal1 = self.setup_table(graph)
        graph, env_goal2 = self.put_fridge(graph, start=False)
        return graph, env_goal1.update(env_goal2)

    def setup_table_put_diswasher(self, graph):
        graph, env_goal1 = self.setup_table(graph)
        graph, env_goal2 = self.put_diswasher(graph, start=False)
        return graph, env_goal1.update(env_goal2)



if __name__ == "__main__":
    # Better to not sue UnityEnv here, it is faster and it allows to create an env without agents
    comm = comm_unity.UnityCommunication()
    comm.reset()
    s, graph = comm.environment_graph()

    ## -------------------------------------------------------------
    ## load task from json, the json file contain max number of objects for each task
    ## -------------------------------------------------------------
    with open('init_pool.json') as file:
        init_pool = json.load(file)

    task_name = random.choice(list(init_pool.keys()))
    goal = {}
    for k,v in init_pool[task_name].items():
        goal[k] = random.randint(0, v)

    ## example setup table
    task_name = 'setup_table'
    goal = {'plates': 2,
            'glasses': 2,
            'wineglass': 1,
            'forks': 0}
    
    ## -------------------------------------------------------------
    ## setup goal based on currect environment
    ## -------------------------------------------------------------
    set_init_goal = SetInitialGoal(goal, obj_position, init_pool[task_name])
    init_graph, env_goal = getattr(set_init_goal, task_name)(graph)
    
    print(env_goal)



    