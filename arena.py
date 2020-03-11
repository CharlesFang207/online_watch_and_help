import random
import pdb

class Arena:
    def __init__(self, agent_types, environment):
        self.agents = []
        for agent_type in agent_types:
            self.agents.append(agent_type)

        self.env = environment

    def reset(self):
        self.env.reset()
        for it, agent in enumerate(self.agents):
            agent.reset(self.env.python_graph, self.env.task_goal, seed=it)

    def get_actions(self, obs):
        dict_actions, dict_info = {}, {}
        op_subgoal = {0: None, 1: None}
        for it, agent in enumerate(self.agents):
            opponent_action = None
            if agent.recursive:
                opponent_action = op_subgoal[it]
            dict_actions[it], dict_info[it] = agent.get_action(obs[it], self.env.task_goal[it], opponent_action)
        return dict_actions, dict_info


    def step(self):
        obs = self.env.get_observations()
        dict_actions, dict_info = self.get_actions(obs)
        print(dict_actions)
        return self.env.step(dict_actions)


    def run(self, random_goal=False):
        task_goal = self.env.task_goal
        if random_goal:
            for predicate in task_goal[0]:
                u = random.choice([0, 1, 2])
                task_goal[0][predicate] = u
                task_goal[1][predicate] = u

        success = False
        while True:
            obs, reward, done, infos = self.step()
            if done:
                success = True