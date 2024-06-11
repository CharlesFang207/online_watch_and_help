import os
import json
import re
from openai import OpenAI

client = OpenAI(
    api_key=''
)

def parse_gpt_response(text, description, episode_num):
    question_pattern = re.compile(r'Question:\s*(.*?)\s*Answer:\s*(.*?)\s*(?=Question:|\Z)', re.DOTALL)
    matches = question_pattern.findall(text)
    questions = {}
    answers = {}
    count = 1
    for match in matches:
        question_content, answer_content = match
        questions[count] = question_content.strip()
        answers[count] = answer_content.strip()
        count += 1

    return {
        episode_num: {
            "description": description,
            "questions": questions,
            "answers": answers
        }
    }

episodes_list = [812]

for episode in episodes_list:
    input_file_path = '/home/scai/Workspace/sye10/virtualHome/online_watch_and_help/GPT/episode_descriptions/episode_{}.txt'.format(episode)

    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"File not found: {input_file_path}")

    with open(input_file_path, 'rb') as file:
        data = file.read()

    data = str(data)

    input_template_list_path = '/home/scai/Workspace/hshi33/virtualhome/data/full_dataset/2_partial_opencost0_closecostFalse_walkcost0.05_forgetrate0_changeroomcost0.5v9_particles_v2/question_types.json'
    episode_key = 'logs_episode.{}_iter.0.pik'.format(episode)
    
    with open(input_template_list_path, 'rb') as file:
        template_list = json.load(file)
    
    if episode_key in template_list:
        templates_to_ask = template_list[episode_key]

    template_question_1 = """
    Question:
    Given the above interaction, if [second agent's name] wants to help [first agent's name] achieve his goal, which of the following locations did [second agent's name] most likely believe the [object second agent mentioned] was located when giving information?
    A) [location second agent mentioned the object was located]
    B) [location that showed up in the episode that was not mentioned by second agent]
    C) [location that did not show up in the episode]
    Answer: A) [location second agent mentioned the object was located]
    """

    template_question_2 = """
    Question:
    Given the above interaction, if [second agent's name] wants to help [first agent's name] achieve his goal, which of the following objects did [second agent's name] most likely believe was [inside/on location that second agent mentioned] when giving information?
    A) [object that showed up in the episode that was not mentioned by second agent]
    B) [object that second agent mentioned was inside the container]
    C) [object that did not show up in the episode]
    Answer: B) [object that second agent mentioned was inside the container]
    """

    template_question_3 = """
    Question:
    Given the above interaction, if [second agent's name] wants to hinder [first agent's name] from achieving his goal, which of the following locations did [second agent's name] least likely believe the [object that second agent mentioned] was located when giving information?
    A) [location that did not show up in the episode]
    B) [location that showed up in the episode that was not mentioned by second agent]
    C) [location second agent mentioned the object was located]
    Answer: C) [location second agent mentioned the object was located]
    """

    template_question_4 = """
    Question:
    Given the above interaction, if [second agent's name] wants to hinder [first agent's name] from achieving his goal, which of the following objects did [second agent's name] least likely believe was located [inside/on location that second agent mentioned] when giving information?
    A) [object that second agent mentioned was inside the container]
    B) [object that showed up in the episode that was not mentioned by second agent]
    C) [object that did not show up in the episode]
    Answer: A) [object that second agent mentioned was inside the container]
    """

    template_question_5 = """
    Question:
    Given the above interaction, assuming that [second agent's name] believes that the [object that second agent mentioned] is [inside/on location that second agent mentioned], when giving information, [second agent's name] is most likely:
    A) Trying to help
    B) Trying to hinder
    C) Neither trying to help nor hinder
    Answer: A) Trying to help
    """

    template_question_6 = """
    Question:
    Given the above interaction, assuming that [second agent's name] believes that nothing worthwhile is [on/inside location that second agent mentioned], when giving information, [second agent's name] is most likely:
    A) Trying to help
    B) Trying to hinder
    C) Neither trying to help nor hinder
    Answer: B) Trying to hinder
    """

    template_question_7 = """
    Question:
    Given the above interaction, assuming that [second agent's name] believes the [object that second agent mentioned] are only in a different location, when giving information, [second agent's name] is most likely:
    A) Trying to help
    B) Trying to hinder
    C) Neither trying to help nor hinder
    Answer: B) Trying to hinder
    """

    instruction = """
    Objective: Generate questions from the language template by filling in the blank.
    User input: A description of the episode.
    Expected output: Questions following this templated format, filling in the blanks, denoted by [] where necessary.

    """

    example_episode = """
    Kevin walked into the kitchen while Alice followed. Kevin then headed to the bedroom as Alice grabbed a carrot. Kevin returned to the kitchen and asked, "Could you help me find the milk and bread? I seem to have misplaced them." Alice responded, "The milk and bread are both inside the kitchen cabinet," as she walked to the kitchen counter and placed the carrot on it.

    Kevin walked to the kitchen cabinet and opened it while Alice opened the fridge. Kevin continued to open more kitchen cabinets as Alice walked to the potatoes. Kevin then opened the stove and grabbed the bread while Alice grabbed a potato. Kevin walked to the fridge and put the bread inside as Alice grabbed another potato. Kevin then walked to the dishwasher and opened it while Alice walked to the kitchen counter and placed the potatoes on it.

    Kevin opened the microwave and then walked back to the bedroom while Alice grabbed another potato and a carrot. Kevin returned to the kitchen as Alice placed the potato on the kitchen counter. Kevin walked to the living room while Alice grabbed another carrot. Kevin returned to the kitchen and walked to the kitchen cabinet, opening it, while Alice placed the carrot on the kitchen counter. Kevin opened another kitchen cabinet and grabbed the milk. Finally, Kevin walked to the fridge and put the milk inside.

    """

    response_question_1 = """
    Question:
    Given the above interaction, if Alice wants to help Kevin achieve his goal, which of the following locations did Alice most likely believe the milk was located when giving information?
    A) Kitchen cabinet
    B) Stove
    C) Coffee table
    Answer: A) Kitchen cabinet
    """

    response_question_2 = """
    Question:
    Given the above interaction, if Alice wants to help Kevin achieve his goal, which of the following objects did Alice most likely believe was inside the Kitchen Cabinet when giving information?
    A) Spoon
    B) Milk
    C) Carrot
    Answer: B) Milk
    """

    response_question_3 = """
    Question:
    Given the above interaction, if Alice wants to hinder Kevin from achieving his goal, which of the following locations did Alice least likely believe the milk was located when giving information?
    A) Coffee table
    B) Stove
    C) Kitchen cabinet
    Answer: C) Kitchen cabinet
    """

    response_question_4 = """
    Question:
    Given the above interaction, if Alice wants to hinder Kevin from achieving his goal, which of the following objects did Alice least likely believe was located inside the kitchen cabinet when giving information?
    A) Milk
    B) Carrot
    C) Spoon
    Answer: A) Milk
    """

    response_question_5 = """
    Question:
    Given the above interaction, assuming that Alice believes that the milk is inside the kitchen cabinet, when giving information, Alice is most likely:
    A) Trying to help
    B) Trying to hinder
    C) Neither trying to help nor hinder
    Answer: A) Trying to help
    """

    response_question_6 = """
    Question:
    Given the above interaction, assuming that Alice believes that nothing worthwhile is inside the kitchen cabinet, when giving information, Alice is most likely:
    A) Trying to help
    B) Trying to hinder
    C) Neither trying to help nor hinder
    Answer: B) Trying to hinder
    """

    response_question_7 = """
    Question:
    Given the above interaction, assuming that [second agent's name] believes the [object that second agent mentioned] are only in a different location, when giving information, [second agent's name] is most likely:
    A) Trying to help
    B) Trying to hinder
    C) Neither trying to help nor hinder
    Answer: B) Trying to hinder
    """

    templates = {
        "1.a.i.1": template_question_1,
        "1.a.i.2": template_question_2,
        "1.a.ii.1": template_question_3,
        "1.a.ii.2": template_question_4,
        "2.a.i": template_question_5,
        "2.a.ii.1": template_question_6,
        "2.a.ii.2": template_question_7
    }

    responses = {
        "1.a.i.1": response_question_1,
        "1.a.i.2": response_question_2,
        "1.a.ii.1": response_question_3,
        "1.a.ii.2": response_question_4,
        "2.a.i": response_question_5,
        "2.a.ii.1": response_question_6,
        "2.a.ii.2": response_question_7
    }

    example_response = ""

    for i, template_num in enumerate(templates_to_ask):
        instruction += templates[template_num]
        example_response += responses[template_num]
        if i < len(templates_to_ask) - 1:
            instruction += "\n"
            example_response += "\n"
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": example_episode},
            {"role": "assistant", "content": example_response},
            {"role": "user", "content": data}
        ],
        model="gpt-4o",
        temperature=0.3
        )
    gpt_output = response.choices[0].message.content.strip()

    json_data = parse_gpt_response(gpt_output, data, episode)

    json_file_path = '/home/scai/Workspace/sye10/virtualHome/online_watch_and_help/GPT/generated_questions/episode_{}.json'.format(episode)

    with open(json_file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

