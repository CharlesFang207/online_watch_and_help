import os
import pickle
import json
import sys
import copy
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

episodes_list = [1143]

for episode in episodes_list:
    pickle_file_path = '/home/scai/Workspace/hshi33/virtualhome/data/full_dataset/1500+episodes/logs_episode.{}_iter.0.pik'.format(episode)

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
    2. Agent names: Make sure to randomize the names. Use a random male name for agent 0 and a random female name for agent 1
    3. Description guidelines: Describe the actions and language of both agents together, step by step. Avoid adjectives and excessive descriptions. Do not skip any action or language steps.
    4. After establishing the timeline, make the description shorter, more concise and flow a lot like a story.
    5. Place more emphasis on the events immediately following the language conversation (if any)
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
    John walked into the kitchen as Emma headed to the living room. He moved to the fridge while Emma approached the table and grabbed a book. "Have you seen the remote control?" John asked, opening the fridge. "I saw it on the sofa," Emma replied, putting down the book. John took the milk from the fridge and closed it, just as Emma walked into the kitchen. Finally, John made his way to the living room.
    """

    user_prompt_1 = """
    {"task_id":2378,"env_id":1,"task_name":"setup_desk_and_prepare_drink","action":{"0":["[grab] <remotecontrol> (330)","[walk] <kitchen> (126)","[walk] <bathroom> (11)","[walk] <livingroom> (261)","[grab] <remotecontrol> (354)","[walk] <desk> (291)","[putback] <remotecontrol> (330) <desk> (291)","[putback] <remotecontrol> (354) <desk> (291)","[walk] <bedroom> (50)","[walk] <book> (331)","[grab] <book> (331)","[walk] <livingroom> (261)","[walk] <desk> (291)","[putback] <book> (331) <desk> (291)"],"1":["[walk] <bedroom> (50)","[walk] <cabinet> (87)","[open] <cabinet> (87)","[grab] <wineglass> (338)","[walk] <coffeetable> (86)","[putback] <wineglass> (338) <coffeetable> (86)","[walk] <kitchen> (126)","[walk] <fridge> (225)","[open] <fridge> (225)","[grab] <alcohol> (353)","[walk] <bedroom> (50)","[putback] <alcohol> (353) <coffeetable> (86)",null,null]},"language":{"0":[null,null,null,"Can you help me find the remote control and the book?",null,null,null,null,null,null,null,null,null,null],"1":[null,null,null,"I'm not sure where the remote control was initially, but I did find it on the coffee table in the living room. As for the book, I spotted one inside the cabinet in the bedroom, although I'm unsure about the location of the other book.",null,null,null,null,null,null,null,null,null,null]},"have_belief":true,"false_belief_rooms":[]}
    """

    response_1 = """
    John grabbed the remote control as Emily walked to the bedroom. He then made his way to the kitchen while Emily headed to the cabinet. John detoured to the bathroom as Emily opened the cabinet. In the living room, John called out, "Can you help me find the remote control and the book?" Emily, taking a wine glass, replied, "I found the remote on the coffee table and a book in the bedroom cabinet."

    John grabbed another remote and went to the desk while Emily placed the wine glass on the coffee table. He put the remote on the desk as Emily walked to the fridge. John continued to the bedroom as Emily retrieved some alcohol from the fridge. He picked up the book while Emily returned to the bedroom to place the alcohol on the coffee table. Finally, John walked to the living room and then to the desk, where he placed the book.
    """

    user_prompt_2 = """
    {"task_id":812,"goals":{"0":{"inside_milk_225":{"count":1,"grab_obj_ids":[338],"container_ids":[225]},"inside_bread_225":{"count":1,"grab_obj_ids":[339],"container_ids":[225]}},"1":{"on_potato_210":{"count":3,"grab_obj_ids":[342,344,346,347,348,349,350,351,352,353,354,355],"container_ids":[210]},"on_carrot_210":{"count":3,"grab_obj_ids":[356,357,358],"container_ids":[210]}}},"action":{"0":["[walk] <kitchen> (126)","[walk] <bedroom> (50)","[walk] <kitchen> (126)","[walk] <kitchencabinet> (206)","[open] <kitchencabinet> (206)","[open] <kitchencabinet> (207)","[open] <kitchencabinet> (208)","[open] <kitchencabinet> (209)","[open] <stove> (226)","[grab] <bread> (339)","[walk] <fridge> (225)","[putin] <bread> (339) <fridge> (225)","[walk] <dishwasher> (228)","[open] <dishwasher> (228)","[open] <microwave> (234)","[walk] <bedroom> (50)","[walk] <kitchen> (126)","[walk] <livingroom> (261)","[walk] <kitchen> (126)","[walk] <kitchencabinet> (203)","[open] <kitchencabinet> (203)","[open] <kitchencabinet> (204)","[grab] <milk> (338)","[walk] <fridge> (225)","[putin] <milk> (338) <fridge> (225)"],"1":["[walk] <kitchen> (126)","[grab] <carrot> (356)","[walk] <kitchencounter> (210)","[putback] <carrot> (356) <kitchencounter> (210)","[open] <fridge> (225)","[walk] <potato> (355)","[grab] <potato> (355)","[grab] <potato> (347)","[walk] <kitchencounter> (210)","[putback] <potato> (355) <kitchencounter> (210)","[putback] <potato> (347) <kitchencounter> (210)","[walk] <potato> (348)","[grab] <potato> (346)","[grab] <carrot> (358)","[putback] <potato> (346) <kitchencounter> (210)","[grab] <carrot> (357)","[putback] <carrot> (358) <kitchencounter> (210)","[putback] <carrot> (357) <kitchencounter> (210)",null,null,null,null,null,null,null]},"finished":true,"language":{"0":[null,"Could you help me find the milk and bread? I seem to have misplaced them.",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null],"1":[null,"The milk and bread are both inside the kitchen cabinet.",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]},"have_belief":false,"false_belief_rooms":[],"fail_to_execute":false}
    """

    response_2 = """
    Kevin walked into the kitchen with Emma following. He went to the bedroom and asked, "Could you help me find the milk and bread?" Emma replied, "They're in the kitchen cabinet," as she grabbed a carrot.

    Kevin returned to the kitchen, opened the cabinet, and searched for the bread. Emma placed the carrot on the counter and opened the fridge. She grabbed a potato while Kevin continued searching. She placed the potato on the counter and grabbed another.

    Kevin found the bread and put it in the fridge. Emma grabbed a potato and a carrot, placing them on the counter. Kevin checked the dishwasher and microwave as Emma continued adding vegetables to the counter.

    Kevin briefly returned to the bedroom, then came back to the kitchen and the living room. He resumed searching the cabinets until he found the milk, which he placed in the fridge.
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
    temperature=1.0
    )

    episode_description = response.choices[0].message.content.strip()

    output_path = f'/home/scai/Workspace/sye10/virtualHome/online_watch_and_help/GPT/episode_descriptions/episode_{episode}_compare.txt'

    with open(output_path,'w') as text_file:
        text_file.write(episode_description)