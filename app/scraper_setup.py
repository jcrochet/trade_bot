import random
import os


# picks one of the user agents or proxies from the provided lists
def get_random_string_from_file(header_type: str) -> str:
    # pass either proxy or user-agent
    search_dir = f"app/{header_type}"
    filenames = [filename for filename in os.listdir(search_dir)]
    # create list to store list of proxies or user-agents
    string_list = []
    # get list of proxies or user-agents by reading each file
    for filename in filenames:
        with open(f"{search_dir}/{filename}", "r") as f:
            for line in f.readlines():
                string_list.append(line.rstrip())
    return random.choice(string_list)
