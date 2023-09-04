import openai
import json
import ast
import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
openai.organization = os.environ.get("OPENAI_ORGANIZATION")
openai.api_key = os.environ.get("OPENAI_API_KEY")


class Node:
    def __init__(self, description):
        self.description = description
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def tree(self, level=0):
        if level == 0:
            ret = "story : " + repr(self.description) + "\n "
            ret += "storyline :" + "\n "
        else:
            ret = " -- " + repr(self.description) + "\n "
        # ret = ""
        for child in self.children:
            ret += child.tree(level + 1)
        return ret


def generate_choices(root_node=None):
    message = [{"role": "user", "content": root_node.tree()},
               {"role": "user", "content": """What could be a potential next outcome for the storyline focused on finishing the story? Output only a python list of very detailed story strings (["..."], without "subtask") of 2 to 5 realistic and possible propositions for the following outcome of the storyline. Each of them should be realistic and very specific. A realistic number of outcomes for the total storyline is around 10 steps."""}]
    print(message)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=message,
        max_tokens=300,  # you can adjust this as needed
    )
    # Assuming the response is newline-separated choices
    print(response.choices[0].message.content)
    choices = ast.literal_eval(response.choices[0].message.content)
    if "STOP" in choices:
        return None
    if type(choices) == str:
        choices = ast.literal_eval(choices)
    choices = [x.replace("'", "").replace('"', '') for x in choices]
    return choices


def check_if_project_is_finished(root_node):
    message = [{"role": "user",
                "content": root_node.tree() + """\n -- \n Is the storyline enough to finish the story? it should at least 8 steps long and have a final conclusion. Output 'STOP' if yes or 'CONTINUE' if not or empty."""}]
    print(message)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=message,
        max_tokens=10,  # you can adjust this as needed
    )
    # Assuming the response is newline-separated choices
    return response.choices[0].message.content


def pick_choice(choices, user_choices):
    print(type(choices), choices)
    print(type(user_choices), user_choices)
    if user_choices.any():
        message = [{"role": "user", "content": "here is a list of previous project and choices of the users: " + str(user_choices)},
               {"role": "user", "content": "output only a directly one single choice as a string from the following list of new choices while trying to mimic previous user behaviours : " + str(choices)}]
    else:
        message = [{"role": "user",
                    "content": "output only a directly a random legit choice from the following choices : " + str(
                        choices)}]

    print(message)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=message,
        max_tokens=300,  # you can adjust this as needed
    )
    # Assuming the response is newline-separated choices
    return response.choices[0].message.content.replace("'", "").replace('"', '')


worker = st.sidebar.selectbox(
    'What mode do you want ?',
    ['Manual', 'Automatic'])

username = st.sidebar.text_input('username')


project = st.sidebar.text_input('project description', key="project")


st.write('you selected this mode:', worker)


def clear_text():
    st.session_state["project"] = ""


reset = st.sidebar.button('Reset',  on_click=clear_text)

if reset:
    project = ""
    st.session_state.current_node = None


st.write('username size : ', int(len(username)))
st.write('project description size : ', int(len(project)))

if username:
    st.write("your username is " + username)

if project:
    st.write("your project description is " + project)
    if "choices_made" not in st.session_state:
        st.session_state.choices_made = [project]
    for value in st.session_state.choices_made[1:]:
        st.write(value)
    # st.write(st.session_state.choices_made)


def troll(index):
    chosen_description = choices[index]
    chosen_node = Node(chosen_description)
    st.session_state.current_node.add_child(chosen_node)
    st.session_state.choices_made += [chosen_description]
    st.session_state.current_node = chosen_node


def save_flow(data, name):
    filename = os.path.join("database.csv")
    with open(filename, 'a') as file:
        file.write(name)
        file.write(";")
        json.dump(data, file)
        file.write('\n')


def load_flows(name):
    filename = os.path.join("database.csv")
    if os.path.isfile(filename):
        df = pd.read_csv("database.csv", header=None, sep=";")
        print(df)
        return df[df[0] == name][1].values
    else:
        return None


if 'stop' not in st.session_state:
    st.session_state.stop = False
if (len(worker) > 1) and (not st.session_state.stop) and (len(username) > 2) and (len(project) > 10):
    if worker == "Manual":
        if "root" not in st.session_state:
            st.session_state.root = Node(project)
        if "current_node" not in st.session_state:
            st.session_state.current_node = st.session_state.root
        while True:
            try:
                stop_check = check_if_project_is_finished(st.session_state.root)
                print(stop_check)
                if (not st.session_state.stop) and ("STOP" in stop_check):
                    save_flow(st.session_state.choices_made.__repr__(), username)
                    st.session_state.stop = True
                    # st.session_state.choices_made = None
                    st.write("Project succesful and saved!")
                choices = generate_choices(st.session_state.root)
                break
            except:
                pass
        if not choices:
            st.write("Project succesful and saved!")
        if not st.session_state.stop and choices:
            for index, choice in enumerate(choices):
                st.button(f"{index + 1}. {choice}", on_click=troll, kwargs={'index': index})
    if worker == "Automatic":
        stop_check_clock = True
        if "root" not in st.session_state:
            st.session_state.root = Node(project)
        if "current_node" not in st.session_state:
            st.session_state.current_node = st.session_state.root
        while True and not st.session_state.stop:
            # try:
                if stop_check_clock:
                    stop_check = check_if_project_is_finished(st.session_state.root)
                print(stop_check)
                if ("STOP" in stop_check):
                    st.session_state.stop = True
                    # save_flow(st.session_state.choices_made.__repr__(), username)
                    # st.session_state.choices_made = None
                    st.write("Project succesful !")
                    break
                else:
                    while True:
                        try:
                            choices = generate_choices(st.session_state.root)
                            break
                        except:
                            pass
                    user_choices = load_flows(username)
                    choice = pick_choice(choices, user_choices)
                    chosen_description = choice
                    chosen_node = Node(chosen_description)
                    st.session_state.current_node.add_child(chosen_node)
                    st.session_state.choices_made += [chosen_description]
                    st.session_state.current_node = chosen_node
                    st.write(chosen_description)
                    stop_check_clock = True
            # except:
            #     stop_check_clock = False
            #     st.write("quick bug")


