import random
import numpy as np
from envs.graph_env import VhGraphEnv
from anytree import AnyNode as Node
import copy
from termcolor import colored
import ipdb
from termcolor import colored


from tqdm import tqdm
from utils import utils_environment as utils_env
import traceback
from evolving_graph.environment import Relation
from utils import utils_exception

class MCTS_particles_v2:
    def __init__(self, gt_graph, agent_id, char_index, max_episode_length, num_simulation, max_rollout_step, c_init, c_base, agent_params, seed=1, add_bp=False):
        self.env = None
        self.discount = 0.95 #0.4
        self.agent_id = agent_id
        self.char_index = char_index
        self.max_episode_length = max_episode_length
        self.num_simulation = num_simulation
        self.max_rollout_step = max_rollout_step
        self.c_init = c_init 
        self.c_base = c_base
        self.seed = 1
        self.add_bp = add_bp
        self.heuristic_dict = None
        self.opponent_subgoal = None
        self.last_opened = None
        self.any_verbose = False
        self.verbose = False
        self.agent_params = agent_params
        self.gt_graph = copy.deepcopy(gt_graph)
        np.random.seed(self.seed)
        random.seed(self.seed)


    def check_progress(self, state, goal_spec):
        """TODO: add more predicate checkers; currently only ON"""
        count = 0
        for key, value in goal_spec.items():
            if key.startswith('off'):
                count += value
        id2node = {node['id']: node for node in state['nodes']}
        class2id = {}

        for node in state['nodes']:
            if node['class_name'] not in class2id:
                class2id[node['class_name']] = []
            class2id[node['class_name']].append(node['id'])
        for key, value in goal_spec.items():
            elements = key.split('_')
            for edge in state['edges']:
                if elements[0] in ['on', 'inside']:
                    if edge['relation_type'].lower() == elements[0] and edge['to_id'] == int(elements[2]) and (id2node[edge['from_id']]['class_name'] == elements[1] or str(edge['from_id']) == elements[1]):
                        count += 1
                elif elements[0] == 'offOn':
                    if edge['relation_type'].lower() == 'on' and edge['to_id'] == int(elements[2]) and (id2node[edge['from_id']]['class_name'] == elements[1] or str(edge['from_id']) == elements[1]):
                        count -= 1
                elif elements[1] == 'offInside':
                    if edge['relation_type'].lower() == 'inside' and edge['to_id'] == int(elements[2]) and (id2node[edge['from_id']]['class_name'] == elements[1] or str(edge['from_id']) == elements[1]):
                        count -= 1
                elif elements[0] == 'holds':
                    if edge['relation_type'].lower().startswith('holds') and id2node[edge['to_id']]['class_name'] == elements[1] and edge['from_id'] == int(elements[2]):
                        count += 1
                elif elements[0] == 'sit':
                    if edge['relation_type'].lower().startswith('on') and edge['to_id'] == int(elements[2]) and edge['from_id'] == int(elements[1]):
                        count += 1
            if elements[0] == 'turnOn':
                if 'ON' in id2node[int(elements[1])]['states']:
                    count += 1
            if elements[0] == 'touch':
                for id_touch in class2id[elements[1]]:
                    if 'TOUCHED' in [st.upper() for st in id2node[id_touch]['states']]:
                        count += 1

        return count
        
    def run(self, curr_root, t, heuristic_dict, plan, opponent_subgoal):
        self.env = VhGraphEnv()
        self.env.pomdp = True
        self.env.reset(copy.deepcopy(self.gt_graph))

        if not self.env.state is None:
            self.id2node_env =  {node['id']: node for node in self.env.state['nodes']}
            static_classes = [
                'bathroomcabinet',
                'kitchencabinet',
                'cabinet',
                'fridge',
                'stove',
                'dishwasher',
                'microwave',
                'kitchentable',
            ]
            self.static_object_ids = [node['id'] for node in self.env.state['nodes'] if node['class_name'] in static_classes]

        state_particle = curr_root.state
        unsatisfied = state_particle[-1]
        #print(colored("Goal:", "green"), curr_root.id[1][0])
        #print(unsatisfied)
        #print(colored('-----', "green"))
        self.opponent_subgoal = copy.deepcopy(opponent_subgoal)
        if self.verbose:
            print('check subgoal')
        

        self.heuristic_dict = heuristic_dict
        # if not curr_root.is_expanded:
        #     belief_set = curr_root.state_set
        #     particle_id = random.randint(0, len(belief_set)-1)
        #     state_particle = belief_set[particle_id]
        #     curr_root = self.expand(curr_root, t, state_particle)
        # self.num_simulation = 100

        # profiler = Profiler()
        # profiler.start()
        last_reward = 0.
        for explore_step in tqdm(range(self.num_simulation)):
            if explore_step % (self.num_simulation - 2) == 0 and explore_step > 0 and self.any_verbose:

                self.verbose = True
            else:
                self.verbose = False
            curr_node = curr_root

            # Select one particle
            state_particle = curr_root.state
            state_graph = state_particle[1]

            # print("Simulation: {}, state_graph {}".format(explore_step, particle_id))
            # if explore_step == 19:
            #     ipdb.set_trace()
            # print([node for node in state_graph['nodes'] if node['id'] == 312])

            node_path = [curr_node]
            state_path = [state_particle]

            tmp_t = t
            
            past_children = curr_node.children
            curr_state = copy.deepcopy(state_particle)


            curr_node, actions = self.expand(curr_node, tmp_t, curr_state)

            #new_children = len(curr_node.children) - len(past_children)

            no_children = False
            # if len(actions) == 0:
            #     ipdb.set_trace()

            it = 0
            costs = [0]
            rewards = [0]
            actions = []
            double_put = False
            while  curr_node.is_expanded:
                # print("Selecting child...", tmp_t)
                # if it == 1:
                #     print('---')
                #     for ch in curr_node.children:

                #         info = self.calculate_score(curr_node, ch, len(actions), info=True)
                #         print('{}, #visit: {}, sc: {}, score: {}, u: {}, q: {}'.format(
                #             ch.id[-1][-1], ch.num_visited, ch.sum_value, info['score'], info['u'], info['q']))
                #     print('--')
                # print(it, actions)
                # ipdb.set_trace()
                if self.verbose:
                    print("Simulation", explore_step, colored("Selecting child...", "blue"))
                    print(len(curr_node.children))
                    print('----')
                next_node, next_state, cost, reward = self.select_child(curr_node, curr_state)
                # if 'put' in actions[-1] and 'put' in actions[-2]:
                #     double_put = True

                # actions_state = [child.id[1][-1] for child in curr_node.children]
                # print(curr_node.id[1][-1], it)
                # ipdb.set_trace()
                # for action in actions_state:
                #     if 'open' in action or 'microwave' in action:
                #         print("OPEN", it, action)
                        # ipdb.set_trace()
                # print('{}, #visit: {}, value: {}'.format(next_node.id[-1][-1], next_node.num_visited, next_node.sum_value))
                if next_node is None:
                    break
                last_reward = reward
                actions.append(next_node.id[1][-1])
                

                it += 1
                
                # if next_node.is_expanded:
                node_path.append(next_node)
                state_path.append(next_state)
                costs.append(cost)
                rewards.append(reward)

                curr_node = next_node
                curr_state = next_state
            
            

            curr_node, _ = self.expand(curr_node, tmp_t + it, curr_state)

            children = [nodech.id[-1][-1] for nodech in curr_node.children]
            # print("expanding", curr_node.id[-1][-1], children)
            if no_children:
                continue
            leaf_node = curr_node
            # print(costs, rewards, tmp_t+it, it)
            verbose_roll = False
            # if leaf_node.id[1][-1] ==  '[open] <fridge> (306)':
            #     verbose_roll = True
            value, reward_rollout, actions_rollout = self.rollout(leaf_node, tmp_t + it, curr_state, last_reward, verbose=verbose_roll)

            # if node_path[-1].id[1][-1] == '[walk] <fridge> (103)' and len(node_path) > 1 and  node_path[-2].id[1][-1] == '[grab] <cupcake> (368)':
            #     print(colored("AQUI", "cyan"))
            #     ipdb.set_trace()

            # if leaf_node.id[1][-1] ==  '[open] <fridge> (306)':
            #     ipdb.set_trace()
            # TODO: is this _Correct
            if double_put:
                raise Exception
                #pass
                # ipdb.set_trace()
            self.backup(value, node_path, costs, rewards, reward_rollout, actions_rollout)
            # print(colored("Finish select", "yellow"))
            
            if explore_step % 198 == 0 and explore_step > 0:

                # self.verbose = True
                pass
                #ipdb.set_trace()
        
        next_root = None
        plan = []
        subgoals = []
        rewards = []
        while curr_root.is_expanded and len(curr_root.children) > 0:

            actions_taken, children_visit, next_root = self.select_next_root(curr_root)
            curr_root = next_root
            plan += [actions_taken]
            
            rewards.append(next_root.sum_value * 1./(next_root.num_visited+1e-9))
            subgoals.append(next_root.id[0])

        # if len(plan) > 0:
        #     elements = plan[0].split(' ')
        #     if need_to_close and (elements[0] == '[walk]' or elements[0] == '[open]' and elements[3] != self.last_opened[1]):
        #         if self.last_opened is not None:
        #             for edge in curr_state_tmp['edges']:
        #                 if edge['relation_type'] == 'CLOSE' and \
        #                     ('({})'.format(edge['from_id']) == self.last_opened[1] and edge['to_id'] == self.agent_id or \
        #                     '({})'.format(edge['to_id']) == self.last_opened[1] and edge['from_id'] == self.agent_id):
        #                     plan = ['[close] {} {}'.format(self.last_opened[0], self.last_opened[1])] + plan
        #                     break
        #     if self.verbose:
        #         print(plan[0])
        if len(plan) > 0 and plan[0].startswith('[open]'):
            elements = plan[0].split(' ')
            self.last_opened = [elements[1], elements[2]]

        # print(colored(plan, 'cyan'))
        # profiler.stop()
        # print(profiler.output_text(unicode=True, color=True))
        # ipdb.set_trace()
        next_root = None
        # ipdb.set_trace()

        # If the goal is to put something inside something

        if len(plan) == 0 and sum([x for x in curr_state[-1].values()]) > 0:
            ipdb.set_trace()
            raise Exception
        # print(plan)
        # if len([x for x in plan if 'grab' in x]) > 1:
        #     ipdb.set_trace()

        return next_root, plan, subgoals, rewards


    def rollout(self, leaf_node, t, state_particle, lrw=0., verbose=False):
        reached_terminal = False

        leaf_node_values = leaf_node.id[1]
        goal_spec, num_steps, actions_parent = leaf_node_values
        curr_vh_state, curr_state, satisfied, unsatisfied = state_particle
        last_reward = lrw
        curr_vh_state = copy.deepcopy(curr_vh_state)

        # TODO: we should start with goals at random, or with all the goals
        # Probably not needed here since we already computed whern expanding node



        rewards = []
        actions_l = []
        subgoals_finished = False
        last_goal = None
        for rollout_step in range(self.max_rollout_step):#min(self.max_rollout_step, self.max_episode_length - t)):
                

            # If you have an object grabbed already reduce the subgoal space search and add the object you already had
            hands_busy = [edge['to_id'] for edge in curr_state['edges'] if 'HOLD' in edge['relation_type']]

            unsatisfied_aux = unsatisfied.copy()
            subgoals_hand = []
            for hand_busy in hands_busy:
                hand_class_name = self.id2node_env[hand_busy]['class_name']
                pred_name_selected = None
                for missing_pred, count_pred in unsatisfied_aux.items():
                    if pred_name_selected is None:
                        if count_pred > 0 and missing_pred.split('_')[1] == hand_class_name:
                            pred_name_selected = missing_pred
                
                if pred_name_selected is not None:
                    unsatisfied_aux[pred_name_selected] -= 1
                    pred_name_split = pred_name_selected.split('_')
                    verb = {'on': 'put', 'inside': 'putIn'}[pred_name_split[0]]
                    subgoals_hand.append(['{}_{}_{}'.format(verb, hand_busy, pred_name_split[2]), pred_name_selected, '{}_{}_{}'.format(pred_name_split[0], hand_busy, pred_name_split[2])])

            subgoals = self.get_subgoal_space(curr_state, satisfied, unsatisfied_aux, self.opponent_subgoal)
            subgoals += subgoals_hand


            # print("Roll", len(subgoals))
            if len(subgoals) == 0:
                subgoals_finished = True
                break


            # If I have 2 hands busy, focus on the objects in 2 hands
            if len(hands_busy) == 2:     
                subgoals = [subg for subg in subgoals if int(subg[0].split('_')[1]) in hands_busy]

            # If I only have 1 hand busy, put this object has to go inside somewhere, focus on it
            # Otherwise it will be impossible to open anything later
            if len(hands_busy) == 1:
                subgoals_putin = [subg for subg in subgoals if int(subg[0].split('_')[1]) == hands_busy[0] and subg[0].split('_')[0].lower() == 'putin']
                if len(subgoals_putin) > 0:
                    subgoals = subgoals_putin
            

            if len(subgoals) == 0:
                raise Exception
                #ipdb.set_trace()
            
            subgoal_list = [x[0] for x in subgoals]
            if last_goal is not None and goal_selected in subgoal_list:
                goal_selected = last_goal

            else:
                curr_goal = random.randint(0, len(subgoals) - 1)
                goal_selected = subgoals[curr_goal][0]
                last_goal = goal_selected

            heuristic = self.heuristic_dict[goal_selected.split('_')[0]]



            actions, _ = heuristic(self.agent_id, self.char_index, unsatisfied, curr_state, self.env, goal_selected)
            if verbose:
                print(hands_busy)
                print("Rollout: ", rollout_step)
                print("Subgoals: ", subgoals, satisfied, unsatisfied)
                print("Goal Selected: ", goal_selected)
                print(actions[0])
                print()
            # if actions[0][1][1] == 333:
            #     print("Plan with glass")
            #     ipdb.set_trace()
            if len(hands_busy) == 2:
                if 'open' in actions[0][0].lower() or 'close' in actions[0][0].lower():
                    actions = None
            # print(actions)

            if actions is None or len(actions) == 0:
                delta_reward = 0
                action = None
            else:
                action = actions[0]
                
                
                action_str = self.get_action_str(action)
                try:
                    success, next_vh_state, next_vh_state_dict, cost, curr_reward = self.transition(curr_vh_state, {0: action_str}, goal_spec)
                except:
                    raise Exception
                    #traceback.print_exc() 
                    #ipdb.set_trace()
                
                if not success:
                    # ipdb.set_trace()
                    print("Failure in transition")
                    raise Exception
                    #ipdb.set_trace()
                    #print("Failure", action_str)
                # print(action_str, cost)
                curr_vh_state, curr_state = next_vh_state, next_vh_state_dict
                delta_reward = curr_reward - last_reward - cost
                
                # print(curr_rewward, last_reward)
                last_reward = curr_reward
            rewards.append(delta_reward)
            actions_l.append(action)

            # print(action_str, curr_reward)
            satisfied, unsatisfied = utils_env.check_progress(curr_state, goal_spec)

            # curr_state = next_state
        # ipdb.set_trace()

        if '<fridge> (103)' in leaf_node.id[-1][-1] and self.any_verbose:
            print("LEAF NODE, rollout")
            print(actions_l)
            print('***')
            # ipdb.set_trace()
        if len(rewards) > 0:
            sum_reward = rewards[-1]
            for r in reversed(rewards[:-1]):
                sum_reward = sum_reward * self.discount + r
        else:
            sum_reward = 0
        # print(sum_reward, reached_terminal)
        # ipdb.set_trace()
        if subgoals_finished:
            pass
            #print(sum_reward, actions_l)
        return sum_reward, rewards, actions_l


    def transition(self, curr_vh_state, action, goal_spec):
        cost = 0.
        # graph = curr_vh_state.to_dict()
        # id2node = {node['id']: node for node in graph['nodes']}
        if 'walk' in action[0]:

            # measure distance, only between rooms
            objects_close = list(curr_vh_state.get_node_ids_from(1, Relation.CLOSE))
            current_room = list(curr_vh_state.get_node_ids_from(1, Relation.INSIDE))[0]
            objects_close_in_room = [obj_id for obj_id in objects_close if current_room in list(curr_vh_state.get_node_ids_from(obj_id, Relation.INSIDE))]
            if True: #len(objects_close_in_room) == 0:
                current_objects = [current_room]
            else:
                current_objects = objects_close_in_room


            action_object_id = int(action[0].split('(')[1].split(')')[0])


            # if the destionation is a room
            if self.id2node_env[action_object_id]['category'] == "Rooms": # or action_object_id in self.static_object_ids:
                current_objects_dest = [action_object_id]
            else:
                objects_on_inside = list(curr_vh_state.get_node_ids_from(action_object_id, Relation.ON)) + list(curr_vh_state.get_node_ids_from(action_object_id, Relation.INSIDE))
                                
                if self.id2node_env[objects_on_inside[0]]['category'] == "Rooms": #len(objects_on_inside) > 0:
                    # The target object is inside something, use that as the location
                    current_objects_dest = objects_on_inside
                else:
                    # get the rooms
                    current_objects_dest = list(curr_vh_state.get_node_ids_from(objects_on_inside[0], Relation.INSIDE))

            # assert len(current_objects_dest) == 0
            # raise Exception
            # Get the center of all the objects you are close to, or the room
            nodes_graph_center = np.concatenate([np.array(self.id2node_env[nodeid]['bounding_box']['center'])[None, :] for nodeid in current_objects], 0)

            # Get the center of the objects close to the dest
            nodes_graph_dest_center = np.concatenate([np.array(self.id2node_env[nodeid]['bounding_box']['center'])[None, :] for nodeid in current_objects_dest], 0)

            center_char = np.mean(nodes_graph_center, 0)
            center_dest = np.mean(nodes_graph_dest_center, 0)

            distance = (center_char - center_dest)**2
            distance = max(np.sqrt(distance[0] + distance[2]), 1)
            # ipdb.set_trace()
            # if self.id2node[action_id]['category'] == "Rooms":
            #    pass
               # cost = 5.0

            # distance = 0
            cost_mult = self.agent_params['walk_cost']
            cost = cost_mult * distance
            
        elif 'open' in action[0]:
            cost = self.agent_params['open_cost']
        elif 'grab' in action[0]:
            cost = 0.05
        elif 'put' in action[0]:
            cost = 0.05
        elif 'touch' in action[0]:
            cost = 0.05
        else:
            print(colored("missing action {}".format(action[0]), "red"))
        # vdict = curr_vh_state.to_dict()
        # print("HANDS", [edge for edge in vdict['edges'] if 'HOLD' in edge['relation_type']])
        success, next_vh_state = self.env.transition(curr_vh_state, action)
        #print(type(next_vh_state), type(curr_vh_state))
        dict_vh_state = next_vh_state.to_dict()
        reward = self.check_progress(dict_vh_state, goal_spec)
        
        return success, next_vh_state, dict_vh_state, cost, reward

    def calculate_score(self, curr_node, child, num_actions, info=False):
        parent_visit_count = curr_node.num_visited
        self_visit_count = child.num_visited
        subgoal_prior = 1.0/num_actions

        if self_visit_count == 0:
            u_score = 1e6 #np.inf
            q_score = 0
        else:
            exploration_rate = np.log((1 + parent_visit_count + self.c_base) /
                                      self.c_base) + self.c_init
            u_score = exploration_rate * subgoal_prior * np.sqrt(
                parent_visit_count) / float(1 + self_visit_count)
            q_score = child.sum_value / self_visit_count

        score = q_score + u_score
        if info:
            return {'score': score, 'q': q_score, 'u': u_score}
        return score


    def select_child(self, curr_node, curr_state):
        # print("Child...", actions)
        possible_children = [child for child in curr_node.children]
        scores = [
            self.calculate_score(curr_node, child, len(possible_children), info=True)
            for child in possible_children
        ]
        scores_info = scores
        scores = [s['score'] for s in scores]

        if len(scores) == 0:
            return None, None, None, None
        maxIndex = np.argwhere(scores == np.max(scores)).flatten()
        selected_child_index = random.choice(maxIndex)
        selected_child = possible_children[selected_child_index]
        
        # 'grab' in curr_node.id[-1][-1] or 
        prev_verbose = False
        if (curr_node.id[-1][-1] == [] or curr_node.id[-1][-1] == '[walk] <cupcake> (369)') and self.any_verbose:
            self.verbose = True

        if self.verbose:
            print("Selecting child for ", curr_node.id[-1][-1])
            print('children_ids:', end='')
            for it, nodech in enumerate(curr_node.children):
                if it != selected_child_index:
                    print(nodech.id[-1][-1], end=', ')
                else:
                    print(colored('{}'.format(nodech.id[-1][-1]), 'yellow'), end=', ')
            print('')
            # print('children_ids:', children_ids)
            # print('children_visit:', children_visit)
            print('children_value:', [s['q'] for s in scores_info])
            print('children_visit:', [s['u'] for s in scores_info])
            print('children_score:', [s['score'] for s in scores_info])
            print('----')

        self.verbose = prev_verbose
        # if 'grab' in curr_node.id[-1][-1]:
        #     ipdb.set_trace()
            
        # print("\nSelecting child...")
        # for it, pc in enumerate(possible_children):
        #     print('{}: {}'.format(pc, scores[it]))

        goal_spec, _, actions = selected_child.id[1]
        # print("selected", actions)
        # print('------\n')
        
        # print("Selecting child,..", actions)

        next_vh_state = curr_state[0]
        # print("\nSelect child")
        # print(actions)
        # print([edge for edge in curr_state[1]['edges'] if edge['from_id'] == 1 and edge['to_id'] == 457])
        # print('.....')
        if selected_child.state is None:

            # print("New action", actions)
            next_vh_state = copy.deepcopy(next_vh_state)

            success, next_vh_state, next_state_dict, cost, reward = self.transition(next_vh_state, {0: actions}, goal_spec)
            # if 'put' in actions:
            #      print("CLOSE:", [edge for edge in next_state_dict['edges'] if edge['to_id'] == 232 and edge['from_id'] == 1])
            if not success:
                print("Failure", actions)
            # final_vh_state = copy.deepcopy(next_vh_state)
            final_vh_state = next_vh_state
            final_state = next_state_dict
            satisfied, unsatisfied = utils_env.check_progress(final_state, goal_spec)
            next_state = (final_vh_state, final_state, satisfied, unsatisfied)
            
            selected_child.state = next_state
            selected_child.cost = cost
            selected_child.reward = reward
        else:
            # success, next_vh_state, cost, reward = self.transition(next_vh_state, {0: actions}, goal_spec)
            # final_state = next_vh_state.to_dict()
            # satisfied, unsatisfied = utils_env.check_progress(final_state, goal_spec)
            # print("CACHE", actions)
            # print("reuse")
            cost = selected_child.cost
            reward = selected_child.reward
            next_state = selected_child.state
            
            # ipdb.set_trace()
        # if 'put' in curr_node.id[1][-1] and '[putback]' in [ch.id[1][-1].split()[0] for ch in possible_children]:
        #     for pci, pc in enumerate(possible_children):
        #         if pc.num_visited == 0:
        #             sc = 0.
        #         else:
        #             sc = pc.sum_value*1.0/pc.num_visited
        #         # print(pc.id[1][-1], sc, scores[pci])
        #     # print(colored(selected_child.id[1][-1], "blue"), reward, cost)

        #     aux_node = selected_child.parent
        #     print(goal_spec)
        #     while aux_node.parent is not None:
        #         print('...', aux_node.id[1][-1])
        #         aux_node = aux_node.parent

        # satisfied, unsatisfied = utils_env.check_progress(final_state, goal_spec)
        # next_state = (final_vh_state, final_state, satisfied, unsatisfied)
        return selected_child, next_state, cost, reward


    def get_subgoal_prior(self, subgoal_space):
        subgoal_space_size = len(subgoal_space)
        subgoal_prior = {
            subgoal: 1.0 / subgoal_space_size
            for subgoal in subgoal_space
        }
        return subgoal_prior


    def expand(self, leaf_node, t, state_particle):
        current_child_actions = []
        if t < self.max_episode_length:
            expanded_leaf_node, current_child_actions = self.initialize_children(leaf_node, state_particle)
            if expanded_leaf_node is not None:
                leaf_node.is_expanded = True
                leaf_node = expanded_leaf_node
        return leaf_node, current_child_actions


    def backup(self, value, node_list, costs, rewards, reward_rollout, actions_rollout):
        t = len(node_list) - 1

        # Compute delta reward
        delta_reward = [0]
        try:
            for i in range(1, len(rewards)):
                delta_reward.append(rewards[i] - rewards[i-1] - costs[i])
        except:
            print(rewards, costs)
            ipdb.set_trace()

        # delta_reward.append(0)
        if len(delta_reward) <= t:
            ipdb.set_trace()

        curr_value = value

        full_backup_actions = [cnode.id[-1][-1] for cnode in node_list]
        backup_actions = [cnode.id[-1][-1].split()[0][1:-1] for cnode in node_list if isinstance(cnode.id[-1][-1], str) ]
        # if ('grab' in backup_actions or '[walk] <cupcake> (369)' in full_backup_actions) and self.any_verbose:
        #     self.verbose = True
        # else:
        #     self.verbose = False


        if self.verbose:
            print(colored("ROLLOUT", "yellow"))
            print(value, reward_rollout, actions_rollout)
            print("======")
        while t >= 0:
            node = node_list[t]
            curr_reward = delta_reward[t]
            # curr_value = curr_value * self.discount + curr_reward
            curr_value += curr_reward
            prev_avg_value = node.sum_value/(node.num_visited+1e-9)
            node.sum_value += curr_value
            node.num_visited += 1

            avg_value = node.sum_value/node.num_visited

            if self.verbose:
                print("Backup", node.id[-1][-1], curr_value, curr_reward, 'avg val:', prev_avg_value, '-->',avg_value)
            
            t -= 1
            # if value > 0:
            #     print(value, [node.id.keys() for node in node_list])
            # print(value, [node.id.keys() for node in node_list])
        if self.verbose:
            # pass
            print('----')


        # if '[walk] <cupcake> (369)' in full_backup_actions:
        #     ipdb.set_trace()


    def select_next_root(self, curr_root):
        children_ids = [child.id[0] for child in curr_root.children]
        children_visit = [child.num_visited for child in curr_root.children]
        children_value = [child.sum_value for child in curr_root.children]

        # print(list([c.id.keys() for c in curr_root.children]))
        maxIndex = np.argwhere(
            children_visit == np.max(children_visit)).flatten()
        selected_child_index = random.choice(maxIndex)
        actions = curr_root.children[selected_child_index].id[1][-1]
        if self.verbose:
            print('children_ids:', [nodech.id[-1][-1] if it != selected_child_index else '**{}**'.format(nodech.id[-1][-1]) for it, nodech in enumerate(curr_root.children)])
            # print('children_ids:', children_ids)
            print('children_visit:', children_visit)
            print('children_value:', children_value)
            print('----')
        return actions, children_visit, curr_root.children[selected_child_index]

    def transition_subgoal(self, satisfied, unsatisfied, subgoal):
        # TODO: do we need this?
        """transition on predicate level"""
        elements = subgoal.split('_')
        if elements[0] == 'put':
            predicate_key = 'on_{}_{}'.format(self.env.id2node[int(elements[1])], elements[2])
            predicate_value = 'on_{}_{}'.format(elements[1], elements[2])
            satisfied[predicate_key].append(satisfied)


    def initialize_children(self, node, state_particle):
        goal_spec = node.id[1][0]
        vh_state, state, satisfied, unsatisfied = state_particle

        # if node.parent is not None and 'put' in node.parent.id[1][-1]:
        #     if node.id is not None:
        #         print("Action", node.id[1][-1])
        #     else:
        #         print("Action", None)
        #     print("CLOSE1:", [edge for edge in state['edges'] if edge['to_id'] == 232 and edge['from_id'] == 1])
        #     print("CLOSE2:", [edge for edge in node.parent.state[1]['edges'] if edge['to_id'] == 232 and edge['from_id'] == 1])

        # print('init child, satisfied:\n', satisfied)
        # print('init child, unsatisfied:\n', unsatisfied)
        
        # ipdb.set_trace()
        # ipdb.set_trace()
        # subgoals = [sg for sg in subgoals if sg[0] != self.opponent_subgoal] # avoid repeating
        # print('init child, subgoals:\n', subgoals)

        # If you have an object grabbed already reduce the subgoal space search and add the object you already had
        curr_state = state
        hands_busy = [edge['to_id'] for edge in curr_state['edges'] if 'HOLD' in edge['relation_type']]

        unsatisfied_aux = unsatisfied.copy()
        subgoals_hand = []
        for hand_busy in hands_busy:
            hand_class_name = self.id2node_env[hand_busy]['class_name']
            pred_name_selected = None
            for missing_pred, count_pred in unsatisfied_aux.items():
                if pred_name_selected is None:
                    if count_pred > 0 and missing_pred.split('_')[1] == hand_class_name:
                        pred_name_selected = missing_pred
            
            if pred_name_selected is not None:
                unsatisfied_aux[pred_name_selected] -= 1
                pred_name_split = pred_name_selected.split('_')
                verb = {'on': 'put', 'inside': 'putIn'}[pred_name_split[0]]
                subgoals_hand.append(['{}_{}_{}'.format(verb, hand_busy, pred_name_split[2]), pred_name_selected, '{}_{}_{}'.format(pred_name_split[0], hand_busy, pred_name_split[2])])

        subgoals = self.get_subgoal_space(curr_state, satisfied, unsatisfied_aux, self.opponent_subgoal)
        subgoals += subgoals_hand

        if len(subgoals) == 0:
            return None, []

        goals_expanded = 0

        current_actions_children = [nodech.id[-1][-1] for nodech in node.children]

        actions_heuristic = []
        current_action = node.id[-1][-1]


        hands_busy = [edge['to_id'] for edge in state_particle[1]['edges'] if 'HOLD' in edge['relation_type']]
        
        if len(hands_busy) == 2:
            subgoals = [subg for subg in subgoals if int(subg[0].split('_')[1]) in hands_busy]

        act_all = []
        for goal_predicate in subgoals:
            goal, predicate, aug_predicate = goal_predicate[0], goal_predicate[1], goal_predicate[2] # subgoal, goal predicate, the new satisfied predicate
            heuristic = self.heuristic_dict[goal.split('_')[0]]
            action_heuristic,  _ = heuristic(self.agent_id, self.char_index, unsatisfied, state, self.env, goal)
            act_all.append((action_heuristic, goal))

            # TODO(xavier): this crashes sometimes!! Check what is happening
            try:
                if ('open' in action_heuristic[0][0].lower() or 'close' in action_heuristic[0][0].lower()) and len(hands_busy) == 2:
                    continue
            except:
                if self.add_bp:
                    ipdb.set_trace()
                raise Exception
            if action_heuristic[0] not in actions_heuristic:
                actions_heuristic.append(self.get_action_str(action_heuristic[0]))

        # if len(hands_bsusy) == 1:
        #     if 'put' in node.id[1][-1]:
        #         aux_node = node
        #         while aux_node.parent is not None:
        #             print(aux_node.id[1][-1])
        #             aux_node = aux_node.parent
                # ipdb.set_trace()
        if len(actions_heuristic) == 0 and node.id[0] is None:
            print("Error, no actions found", subgoals)
            raise Exception

        # if node.id[1][-1] == '[open] <fridge> (306)' and len(hands_busy) == 1:
        #     ipdb.set_trace()

        for action in actions_heuristic:
            
            # If I already expanded this child, no need to re-expand
            action_str = action
            if action_str in current_actions_children:
                continue

            # print(goal_predicate, cost)
            # next_vh_state = copy.deepcopy(vh_state)
            # actions_str = []

            
            # next_vh_state = self.env.transition(next_vh_state, {0: action_str})
            # goals_expanded += 1

            # next_satisfied = copy.deepcopy(satisfied)
            # next_unsatisfied = copy.deepcopy(unsatisfied)
            # if aug_predicate is not None:
            #     next_satisfied[predicate].append(aug_predicate)
            # next_unsatisfied[predicate] -= 1
            # belief_states = [next_vh_state, next_vh_state.to_dict(), next_satisfied, next_unsatisfied]


            new_node = Node(
                parent=node,
                id=("Child", [goal_spec, len(actions_heuristic), action_str]),
                state=None,
                num_visited=0,
                sum_value=0,
                subgoal_prior=1.0 / 1.0,
                is_expanded=False)


        
        # ipdb.set_trace()
        # if goals_expanded == 0:
        #     return None, []
        return node, actions_heuristic

    def get_action_str(self, action_tuple):
        obj_args = [x for x in list(action_tuple)[1:] if x is not None]
        objects_str = ' '.join(['<{}> ({})'.format(x[0], x[1]) for x in obj_args])
        return '[{}] {}'.format(action_tuple[0], objects_str)

    def get_subgoal_space(self, state, satisfied, unsatisfied, opponent_subgoal=None, verbose=0):
        """
        Get subgoal space
        Args:
            state: current state
            satisfied: satisfied predicates
            unsatisfied: # of unstatisified predicates
        Returns:
            subgoal space
        """
        """TODO: add more subgoal heuristics; currently only have (put x y)"""
        # print('get subgoal space, state:\n', state['nodes'])

        obs = self.env._mask_state(state, self.char_index)
        obsed_objs = [node["id"] for node in obs["nodes"]]

        inhand_objects = []
        for edge in state['edges']:
            if edge['relation_type'].startswith('HOLDS') and \
                edge['from_id'] == self.agent_id:
                inhand_objects.append(edge['to_id'])
        inhand_objects_opponent = []
        for edge in state['edges']:
            if edge['relation_type'].startswith('HOLDS') and \
                edge['from_id'] == 3 - self.agent_id:
                inhand_objects_opponent.append(edge['to_id'])

        # if verbose:
        #     print('inhand_objects:', inhand_objects)
        #     print(state['edges'])

        id2node = {node['id']: node for node in state['nodes']}
        class2id = {}
        for node in state['nodes']:
            if node['class_name'] not in class2id:
                class2id[node['class_name']] = []
            class2id[node['class_name']].append(node['id'])


        opponent_predicate_1 = None
        opponent_predicate_2 = None
        if opponent_subgoal is not None:
            elements = opponent_subgoal.split('_')
            if elements[0] in ['put', 'putIn']:
                obj1_class = None
                for node in state['nodes']:
                    if node['id'] == int(elements[1]):
                        obj1_class = node['class_name']
                        break
                # if obj1_class is None:
                #     opponent_subgoal = None
                # else:
                opponent_predicate_1 = '{}_{}_{}'.format('on' if elements[0] == 'put' else 'inside', obj1_class, elements[2])
                opponent_predicate_2 = '{}_{}_{}'.format('on' if elements[0] == 'put' else 'inside', elements[1], elements[2])

        subgoal_space, obsed_subgoal_space, overlapped_subgoal_space = [], [], []
        # ipdb.set_trace()
        for predicate, count in unsatisfied.items():
            obj_grabbed = False
            if count > 1 or count > 0 and predicate not in [opponent_predicate_1, opponent_predicate_2]:
                elements = predicate.split('_')
                # print(elements)
                if elements[0] == 'on':
                    subgoal_type = 'put'
                    obj = elements[1]
                    surface = elements[2] # assuming it is a graph node id
                    for node in state['nodes']:
                        if node['class_name'] == obj or str(node['id']) == obj:
                            # print(node)
                            # if verbose:
                            #     print(node)
                            tmp_predicate = 'on_{}_{}'.format(node['id'], surface) 
                            if tmp_predicate not in satisfied[predicate]:
                                tmp_subgoal = '{}_{}_{}'.format(subgoal_type, node['id'], surface)
                                if tmp_subgoal != opponent_subgoal:
                                    subgoal_space.append(['{}_{}_{}'.format(subgoal_type, node['id'], surface), predicate, tmp_predicate])
                                    if node['id'] in obsed_objs:
                                        obsed_subgoal_space.append(['{}_{}_{}'.format(subgoal_type, node['id'], surface), predicate, tmp_predicate])
                                    if node['id'] in inhand_objects:
                                        pass
                                        # return [subgoal_space[-1]]
                elif elements[0] == 'inside':
                    subgoal_type = 'putIn'
                    obj = elements[1]
                    surface = elements[2] # assuming it is a graph node id
                    for node in state['nodes']:
                        if node['class_name'] == obj or str(node['id']) == obj:
                            # if verbose:
                            #     print(node)
                            tmp_predicate = 'inside_{}_{}'.format(node['id'], surface) 
                            if tmp_predicate not in satisfied[predicate]:
                                tmp_subgoal = '{}_{}_{}'.format(subgoal_type, node['id'], surface)
                                if tmp_subgoal != opponent_subgoal:
                                    subgoal_space.append(['{}_{}_{}'.format(subgoal_type, node['id'], surface), predicate, tmp_predicate])
                                    if node['id'] in obsed_objs:
                                        obsed_subgoal_space.append(['{}_{}_{}'.format(subgoal_type, node['id'], surface), predicate, tmp_predicate])
                                    if node['id'] in inhand_objects:
                                        obj_grabbed = True
                                        pass
                                        # return [subgoal_space[-1]]
                elif elements[0] == 'offOn':
                    if id2node[elements[2]]['class_name'] in ['dishwasher', 'kitchentable']:
                        containers = [[node['id'], node['class_name']] for node in state['nodes'] if node['class_name'] in ['kitchencabinets', 'kitchencounterdrawer', 'kitchencounter']]
                    else:
                        containers = [[node['id'], node['class_name']] for node in state['nodes'] if node['class_name'] == 'coffetable']
                    for edge in state['edges']:
                        if edge['relation_type'] == 'ON' and edge['to_id'] == int(elements[2]) and id2node[edge['from_id']]['class_name'] == elements[1]:
                            container = random.choice(containers)
                            predicate = '{}_{}_{}'.format('on' if container[1] == 'kitchencounter' else 'inside', edge['from_id'], container[0])
                            goals[predicate] = 1
                elif elements[0] == 'offInside':
                    if id2node[elements[2]]['class_name'] in ['dishwasher', 'kitchentable']:
                        containers = [[node['id'], node['class_name']] for node in state['nodes'] if node['class_name'] in ['kitchencabinets', 'kitchencounterdrawer', 'kitchencounter']]
                    else:
                        containers = [[node['id'], node['class_name']] for node in state['nodes'] if node['class_name'] == 'coffetable']
                    for edge in state['edges']:
                        if edge['relation_type'] == 'INSIDE' and edge['to_id'] == int(elements[2]) and id2node[edge['from_id']]['class_name'] == elements[1]:
                            container = random.choice(containers)
                            predicate = '{}_{}_{}'.format('on' if container[1] == 'kitchencounter' else 'inside', edge['from_id'], container[0])
                            goals[predicate] = 1
                elif elements[0] == 'touch':
                    for n_id in class2id[elements[1]]:
                        if 'TOUCHED' not in [st.upper() for st in id2node[n_id]['states']]:
                            tmp_predicate = 'touch_{}_{}'.format(n_id, 1)
                            subgoal_space.append(['touch_{}'.format( n_id), predicate, tmp_predicate])

            elif predicate in [opponent_predicate_1, opponent_predicate_2] and len(inhand_objects_opponent) == 0:
                elements = predicate.split('_')
                # print(elements)
                if elements[0] == 'on':
                    subgoal_type = 'put'
                    obj = elements[1]
                    surface = elements[2] # assuming it is a graph node id
                    for node in state['nodes']:
                        if node['class_name'] == obj or str(node['id']) == obj:
                            tmp_predicate = 'on_{}_{}'.format(node['id'], surface) 
                            if tmp_predicate not in satisfied[predicate]:
                                tmp_subgoal = '{}_{}_{}'.format(subgoal_type, node['id'], surface)
                                overlapped_subgoal_space.append(['{}_{}_{}'.format(subgoal_type, node['id'], surface), predicate, tmp_predicate])                        
                elif elements[0] == 'inside':
                    subgoal_type = 'putIn'
                    obj = elements[1]
                    surface = elements[2] # assuming it is a graph node id
                    for node in state['nodes']:
                        if node['class_name'] == obj or str(node['id']) == obj:
                            tmp_predicate = 'inside_{}_{}'.format(node['id'], surface) 
                            if tmp_predicate not in satisfied[predicate]:
                                tmp_subgoal = '{}_{}_{}'.format(subgoal_type, node['id'], surface)
                                overlapped_subgoal_space.append(['{}_{}_{}'.format(subgoal_type, node['id'], surface), predicate, tmp_predicate])
                                    
        if len(obsed_subgoal_space) > 0:
            pass
            #return obsed_subgoal_space
        if len(subgoal_space) == 0:
            # if self.agent_id == 2 and verbose == 1:
            #     ipdb.set_trace()
            if len(overlapped_subgoal_space) > 0:
                return overlapped_subgoal_space
            for predicate, count in unsatisfied.items():
                if count == 1:
                    elements = predicate.split('_')
                    # print(elements)
                    if elements[0] == 'turnOn':
                        subgoal_type = 'turnOn'
                        obj = elements[1]
                        for node in state['nodes']:
                            if node['class_name'] == obj or str(node['id']) == obj:
                                # print(node)
                                # if verbose:
                                #     print(node)
                                tmp_predicate = 'turnOn{}_{}'.format(node['id'], 1) 
                                if tmp_predicate not in satisfied[predicate]:
                                    subgoal_space.append(['{}_{}'.format(subgoal_type, node['id']), predicate, tmp_predicate])
        if len(subgoal_space) == 0:
            for predicate, count in unsatisfied.items():
                if count == 1:
                    elements = predicate.split('_')
                    # print(elements)
                    if elements[0] == 'holds' and int(elements[2]) == self.agent_id:
                        subgoal_type = 'grab'
                        obj = elements[1]
                        for node in state['nodes']:
                            if node['class_name'] == obj or str(node['id']) == obj:
                                # print(node)
                                # if verbose:
                                #     print(node)
                                tmp_predicate = 'holds_{}_{}'.format(node['id'], 1) 
                                if tmp_predicate not in satisfied[predicate]:
                                    subgoal_space.append(['{}_{}'.format(subgoal_type, node['id']), predicate, tmp_predicate])
        if len(subgoal_space) == 0:
            for predicate, count in unsatisfied.items():
                if count == 1:
                    elements = predicate.split('_')
                    # print(elements)
                    if elements[0] == 'sit' and int(elements[1]) == self.agent_id:
                        subgoal_type = 'sit'
                        obj = elements[2]
                        for node in state['nodes']:
                            if node['class_name'] == obj or str(node['id']) == obj:
                                # print(node)
                                # if verbose:
                                #     print(node)
                                tmp_predicate = 'sit_{}_{}'.format(1, node['id']) 
                                if tmp_predicate not in satisfied[predicate]:
                                    subgoal_space.append(['{}_{}'.format(subgoal_type, node['id']), predicate, tmp_predicate])

        # if obj_grabbed:
        #     ipdb.set_trace()
        return subgoal_space




        
