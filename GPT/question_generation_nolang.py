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

episodes_list = [3437, 2709, 766, 1859, 404, 3367, 1917, 2726, 2808, 640, 549, 609, 538, 3289, 
                3096, 3412, 135, 2053, 801, 857, 144, 3128, 3082, 3325, 138, 3115, 3312, 3372, 
                2826, 642, 2719, 182, 3355, 3068, 153, 1827, 3031, 1797, 3056, 3179, 3462, 263, 
                221, 647, 557, 398, 1886, 784, 240, 3308, 913, 1931, 2079, 1134, 130, 3212, 3395, 
                634, 3058, 644, 1851, 395, 195, 3475, 202, 895, 1775, 3092, 3391, 780, 541, 407, 
                147, 865, 3197, 389, 128, 2448, 3157, 154, 628, 3117, 3371, 2447, 2780, 223, 3129, 
                1883, 212, 2070, 858, 393, 1856, 3438, 2584, 3292, 578, 1848, 2559, 2474, 571, 1802, 
                548, 1825, 225, 608, 218, 910, 2799, 956, 3145, 42, 193, 2462, 3366, 211, 1758, 161, 
                1818, 1867, 2801, 3081, 949, 406, 3300, 3533, 3419, 397, 630, 956, 417, 3130, 3315, 
                612, 3098, 3074, 2829, 1798, 121, 3166, 2473, 240, 892, 2701, 149, 905, 801, 1861, 3119, 
                179, 3398, 869, 1131, 129, 1817, 871, 2748, 1140, 1894, 3423, 3328, 532, 2512, 854, 583, 
                1819, 949, 1892, 152, 1880, 655, 824, 3080, 906, 3063, 2759, 1811, 2542, 2050, 3077, 550, 
                650, 577, 2813, 3070, 790, 1858, 848, 3050, 3433, 1860, 767, 3060, 3478, 3047, 3344, 3065, 
                569, 528, 682, 2045, 2624, 931, 1865, 3323, 3140, 1765, 1813, 2556, 3536, 601, 2536, 931, 
                1893, 1919, 3384, 564, 3090, 3324]

for episode in episodes_list:
    input_file_path = '/home/scai/Workspace/sye10/virtualHome/online_watch_and_help/GPT/episode_descriptions_no_lang/episode_{}.txt'.format(episode)

    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"File not found: {input_file_path}")

    with open(input_file_path, 'rb') as file:
        data = file.read()

    data = str(data)

    episode_key = 'logs_episode.{}_iter.0.pik'.format(episode)
    

    instruction = """
    Objective: Generate questions from the language template by filling in the blank.
    User input: A description of the episode.
    Expected output: Questions following this templated format, filling in the blanks, denoted by [] where necessary.

    Question:
    Given the above interaction, if [second agent's name] believes that [first agent's name]'s goal is to place [an object placed by first agent and then moved by second agent] [inside/on location that first agent place that object], [second agent's name] is least likely
    A) Helping [first agent's name]
    B) Hindering [first agent's name]
    C) Neither helping nor hindering

    Answer: A) Helping [first agent's name]

    Question:
    Given the above interaction, if [second agent's name] believes that [first agent's name]'s goal is to place [an object placed by first agent and then moved by second agent] [inside/on location that second agent finally place that object], [second agent's name] is least likely
    A) Helping [first agent's name]
    B) Hindering [first agent's name]
    C) Neither helping nor hindering

    Answer: B) Hindering [first agent's name]

    Question:
    Given the above interaction, if [second agent's name] wants to help [first agent's name], [second agent's name]'s most likely believed goal of [first agent's name] is
    A) Placing [an object placed by first agent and then moved by second agent] [on/inside place that first agent place the object]
    B) Placing [the same object as before] [on/inside the place that second agent place the object]
    C) Placing [the same object as before] [on/inside another reasonable location where agents never interact with]

    Answer: B) Placing [the same object as before] [on/inside the place that second agent place the object]

    Question:
    Given the above interaction, if [second agent's name] wants to hinder [first agent's name], [second agent's name]'s least likely believed goal of [first agent's name] is
    A) Placing [an object placed by first agent and then moved by second agent] [on/inside place that first agent place the object]
    B) Placing [the same object as before] [on/inside the place that second agent place the object]
    C) Placing [the same object as before] [on/inside another reasonable location where agents never interact with]

    Answer: B) Placing [the same object as before] [on/inside place that second agent place the object]

    """

    example_episode = """
    David walked into the kitchen, grabbed a spoon, and then headed to the fridge. He opened the fridge, grabbed a bottle of wine, and walked through several rooms: bedroom, another bedroom, bathroom, and then the living room. He placed the wine on the coffee table in the living room and went back to the bathroom.

    Meanwhile, Sophia eventually walked into the kitchen, approached a kitchen cabinet, opened it, and grabbed a wineglass. She opened the dishwasher and placed the wineglass inside. She again opened a kitchen cabinet and took a spoon, placing it next to the wineglass in the dishwasher. She grabbed another wineglass from a different cabinet, walked back to the dishwasher, and put the wineglass inside. Sophia headed to the living room, grabbed another spoon placed by David, walked back to the kitchen and placed that inside the dishwasher as well.

    """

    example_response = """
    
    Question:
    Given the above interaction, if Sophia believes that David's goal is to place spoon on coffeetable, Sophia is least likely
    A) Helping David
    B) Hindering David
    C) Neither helping nor hindering

    Answer: A) Helping David

    Question:
    Given the above interaction, if Sophia believes that David's goal is to place spoon inside dishwasher, Sophia is least likely
    A) Helping David
    B) Hindering David
    C) Neither helping nor hindering

    Answer: B) Hindering David

    Question:
    Given the above interaction, if Sophia wants to help David, Sophia's most likely believed goal of David is
    A) Placing spoon on coffeetable
    B) Placing spoon inside dishwasher
    C) Placing spoon inside kitchen cabinet

    Answer: B) Placing spoon inside dishwasher

    Question:
    Given the above interaction, if Sophia wants to hinder David, Sophia's least likely believed goal of David is
    A) Placing spoon on coffeetable
    B) Placing spoon inside dishwasher
    C) Placing spoon inside kitchen cabinet

    Answer: B) Placing spoon inside dishwasher
    """
    
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

