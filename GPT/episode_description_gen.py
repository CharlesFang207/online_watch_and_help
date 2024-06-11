import os
import pickle
import json
import sys
import copy
from openai import OpenAI

client = OpenAI(
    api_key=''
)

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{curr_dir}/../../online_watch_and_help/")
from agents import language
sys.path.insert(0, f"{curr_dir}/")

def remove_sections(data, keys_to_remove):
    for key in keys_to_remove:
        if key in data:
            del data[key]

episodes_list = [812]

for episode in episodes_list:
    pickle_file_path = '/home/scai/Workspace/hshi33/virtualhome/data/full_dataset/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2/logs_episode.{}_iter.0.pik'.format(episode)

    if not os.path.exists(pickle_file_path):
        raise FileNotFoundError(f"File not found: {pickle_file_path}")

    with open(pickle_file_path, 'rb') as file:
        data = pickle.load(file)
        
    if data["fail_to_execute"]:
        print("Episode {} has failed to execute".format(episode))
        continue
    keys_to_remove = ['gt_goals','init_unity_graph','plan','goals_finished','belief','belief_room','belief_graph', 'graph','obs', "env_id", "task_name", "language_object"]

    remove_sections(data, keys_to_remove)

    json_file_path = f'/home/scai/Workspace/sye10/virtualHome/online_watch_and_help/GPT/pipelined_data/episode_{episode}.json'

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, separators=(',', ':'))

    instruction_prompt = """
    Objective: Create a description of a two-agent interaction scenario based on the provided language template.
    User Input: A list of actions by each agent, Verbal communication between the agents.
    Structure: Actions: A list of actions taken by agent 0 and agent 1, Language: Verbal communication between the agents in a list format.
    Instructions:
    1. Synchronization guidelines: Synchronize actions and language, the first entry in the "language" list corresponds to the first action step, the second entry in the "language" list corresponds to the second action and so on. If a language entry is null, there is no communication at that timestep. Synchronize descriptions of actions and language strictly by timesteps.
    2. Agent names: Use a random male name for agent 0 and a random female name for agent 1
    3. Description guidelines: Describe the actions and language of both agents together, step by step. Avoid adjectives and excessive descriptions. Do not skip any action or language steps.
    """

    further_instructions = """
    Note that the first action of agent 0 occurs at the same time as the first action of agent 1, and so on.
    For example, reason through the user's input like this before generating the response. 
    Actions: 0: ["[walk] <kitchen> (111)", "[walk] <fridge> (157)", "[open] <fridge> (157)", "[grab] <milk> (387)", "[close] <fridge> (157)", "[walk] <livingroom> (101)"]
    1: ["[walk] <livingroom> (101)", "[walk] <table> (138)", "[grab] <book> (377)", "[putdown] <book> (377) <table> (138)", "[walk] <kitchen> (111)"]
    Language: 0: [null, null, null, "Have you seen the remote control?", null, null] 1: [null, null, null, "I saw a remote control on the sofa", null, null]
    Description:
    First timestep: John walks into the kitchen while Emma heads to the living room. (No language communication)
    Second timestep: John walks to the fridge as Emma approaches the table. (No language communication)
    Third timestep: John opens the fridge while Emma grabs a book from the table. "Have you seen the remote control?" John asks. "I saw a remote control on the sofa" Emma responds.
    Fourth timestep: John grabs the milk from the fridge. Emma puts down the book. (No language communication)
    Fifth timestep: John closes the fridge. Emma walks to the kitchen (No language communication)
    Sixth timestep: John walks into the living room (No language communication)
    Generated response:
    John walked into the kitchen while Emma headed to the living room. Then, John moved to the fridge as Emma approached the table. John opened the fridge while Emma grabbed a book from the table. "Have you seen the remote control?" John asked. "I saw a remote control on the sofa," Emma responded. John grabbed the milk from the fridge as Emma put down the book. He closed the fridge while Emma walked to the kitchen. Finally, John walked into the living room.
    """

    user_prompt_1 = """
    {"task_id":2378,"env_id":1,"task_name":"setup_desk_and_prepare_drink","action":{"0":["[grab] <remotecontrol> (330)","[walk] <kitchen> (126)","[walk] <bathroom> (11)","[walk] <livingroom> (261)","[grab] <remotecontrol> (354)","[walk] <desk> (291)","[putback] <remotecontrol> (330) <desk> (291)","[putback] <remotecontrol> (354) <desk> (291)","[walk] <bedroom> (50)","[walk] <book> (331)","[grab] <book> (331)","[walk] <livingroom> (261)","[walk] <desk> (291)","[putback] <book> (331) <desk> (291)"],"1":["[walk] <bedroom> (50)","[walk] <cabinet> (87)","[open] <cabinet> (87)","[grab] <wineglass> (338)","[walk] <coffeetable> (86)","[putback] <wineglass> (338) <coffeetable> (86)","[walk] <kitchen> (126)","[walk] <fridge> (225)","[open] <fridge> (225)","[grab] <alcohol> (353)","[walk] <bedroom> (50)","[putback] <alcohol> (353) <coffeetable> (86)",null,null]},"language":{"0":[null,null,null,"Can you help me find the remote control and the book?",null,null,null,null,null,null,null,null,null,null],"1":[null,null,null,"I'm not sure where the remote control was initially, but I did find it on the coffee table in the living room. As for the book, I spotted one inside the cabinet in the bedroom, although I'm unsure about the location of the other book.",null,null,null,null,null,null,null,null,null,null]},"have_belief":true,"false_belief_rooms":[]}
    """

    response_1 = """
    John grabbed the remote control as Emily walked to the bedroom. Then, John made his way to the kitchen while Emily headed to the cabinet. As John proceeded to the bathroom, Emily opened the cabinet. Moving to the living room, John asked, "Can you help me find the remote control and the book?" Emily, grabbing a wine glass from the cabinet, responded, "I'm not sure where the remote control was initially, but I did find it on the coffee table in the living room. As for the book, I spotted one inside the cabinet in the bedroom, although I'm unsure about the location of the other book." John grabbed another remote control and walked to the desk while Emily walked to the coffee table and placed the wine glass on it. John then placed the remote control on the desk as Emily moved to the kitchen. Next, John put another remote control on the desk while Emily walked to the fridge and opened it. John proceeded to the bedroom as Emily grabbed the alcohol from the fridge. John then walked to the book and grabbed it while Emily returned to the bedroom and put the alcohol on the coffee table. Finally, John walked to the living room and then to the desk, where he placed the book.
    """

    user_prompt_2 = """
    {"task_id":955,"action":{"0":["[walk] <kitchen> (111)","[walk] <kitchencabinet> (144)","[open] <kitchencabinet> (143)","[open] <kitchencabinet> (144)","[walk] <bedroom> (214)","[walk] <bread> (387)","[grab] <bread> (387)","[walk] <kitchen> (111)","[walk] <fridge> (157)","[open] <fridge> (157)","[putin] <bread> (387) <fridge> (157)",null,null,null],"1":["[walk] <cabinet> (275)","[open] <cabinet> (275)","[walk] <kitchen> (111)","[walk] <potato> (382)","[grab] <potato> (382)","[putback] <potato> (382) <kitchentable> (138)","[open] <kitchencabinet> (147)","[open] <kitchencabinet> (148)","[grab] <potato> (384)","[putback] <potato> (384) <kitchentable> (138)","[grab] <carrot> (385)","[putback] <carrot> (385) <kitchentable> (138)","[grab] <carrot> (386)","[putback] <carrot> (386) <kitchentable> (138)"]},"language":{"0":[null,null,null,"Would you happen to know where the bread is?",null,null,null,null,null,null,null,null,null,null],"1":[null,null,null,"I found some bread inside a cabinet in the bedroom.",null,null,null,null,null,null,null,null,null,null]},"have_belief":true,"false_belief_rooms":["kitchen"]}
    """

    response_2 = """
    Kevin walked into the kitchen while Alice headed to the cabinet. Then, Kevin walked to the kitchen cabinet as Alice opened it. Kevin opened the kitchen cabinet while Alice walked to the kitchen. "Would you happen to know where the bread is?" Kevin asked. "I found some bread inside a cabinet in the bedroom," Alice responded as she walked to the potatoes. Kevin opened another kitchen cabinet while Alice grabbed a potato. Kevin then walked to the bedroom as Alice put the potato back on the kitchen table.

    Kevin walked to the bread while Alice opened the kitchen cabinet again. He grabbed the bread as Alice opened another kitchen cabinet. Kevin returned to the kitchen while Alice grabbed the potato again. Kevin walked to the fridge as Alice put the potato back on the kitchen table. He opened the fridge while Alice grabbed a carrot. Kevin put the bread in the fridge as Alice put the carrot back on the kitchen table. Finally, Alice grabbed another carrot and put it back on the kitchen table.
    """

    with open(json_file_path, 'r') as json_file:
        final_prompt = json_file.read()

    response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": instruction_prompt},
        {"role": "system", "content": further_instructions},
        {"role": "user", "content": user_prompt_1},
        {"role": "assistant", "content": response_1},
        {"role": "user", "content": user_prompt_2},
        {"role": "assistant", "content": response_2},
        {"role": "user", "content": final_prompt}
    ],
    model="gpt-4o",
    temperature=0.3
    )

    episode_description = response.choices[0].message.content.strip()

    output_path = f'/home/scai/Workspace/sye10/virtualHome/online_watch_and_help/GPT/episode_descriptions/episode_{episode}.txt'

    with open(output_path,'w') as text_file:
        text_file.write(episode_description)