import argparse
import os
import random
import json
from os.path import join


parser = argparse.ArgumentParser(description="Randomly choose several histories for manual checking")
parser.add_argument("--results_parent_folder", help="Directory with all the repositories' results", required=True)
parser.add_argument("--output_json_file", help="a json file to write chosen histories", required=True)


def random_select_repositories(results_parent_folder):
    repositories = [
        f for f in os.listdir(results_parent_folder) if os.path.isdir(os.path.join(results_parent_folder, f))
    ]
    # To ensure reproducibility, use a fixed seed value with the random module
    seed_value = 42
    random.seed(seed_value)

    # Check at least ~25% of the repositories
    num_repositories = len(repositories)
    num_repositories_to_choose = random.randint(num_repositories // 4, num_repositories)
    chosen_repositories = random.sample(repositories, num_repositories_to_choose)
    print(f"Number of repositories chosen: {num_repositories_to_choose}")
    print(f"Chosen repositories: {chosen_repositories}")

    return num_repositories_to_choose, chosen_repositories

def write_chosen_info(output_json_file, to_write):
    with open(output_json_file, "a", newline="\n") as f:
        f.write(f"{to_write}\n")


class SelectHistoriesManualCheck:
    def __init__(self, repo, history_json_file, output_json_file):
        self.repo = repo
        self.history_json_file = history_json_file
        self.output_json_file = output_json_file

    def random_select_histories(self):
        with open(self.history_json_file, 'r') as f:
            data = json.load(f)

        seed_value = 30
        random.seed(seed_value)

        whole_history_length = len(data)
        max_num = whole_history_length % 10
        if whole_history_length < max_num:
            # not able to get max_num histories
            max_num = whole_history_length
        if max_num == 0:  # whole_history_length: times of 10
            max_num = random.randint(2, 10)
        elif max_num == 1:
            max_num += 1  # to fit the range
        max_num_histories_to_choose = random.randint(1, max_num)

        num_histories_to_choose = random.randint(1, max_num_histories_to_choose)
        chosen_histories = random.sample(data, num_histories_to_choose)
        print(f"Number of histories chosen: {self.repo} {num_histories_to_choose}")
        self.write_selected_histories(chosen_histories, num_histories_to_choose)

        return num_histories_to_choose

    def write_selected_histories(self, chosen_histories, num_histories_to_choose):
        with open(self.output_json_file, "a", newline="\n") as f:
            f.write(f"{self.repo}: {num_histories_to_choose}\n")
            json.dump(chosen_histories, f, indent=4, ensure_ascii=False)
            f.write("\n")


def main(results_parent_folder, output_json_file):
    num_repositories_to_choose, chosen_repositories = random_select_repositories(results_parent_folder)
    write_chosen_info(output_json_file, f"All chosen repositories: {num_repositories_to_choose}.\n{chosen_repositories}")
    all_chosen_histories_num = 0
    for repo in chosen_repositories:
        history_json_file = join(results_parent_folder, repo, "histories_suppression_level_all.json")
        if os.path.exists(history_json_file):
            num_histories_to_choose = SelectHistoriesManualCheck(repo, history_json_file, output_json_file).random_select_histories()
            all_chosen_histories_num += num_histories_to_choose
    print(f"Number of histories chosen (all): {all_chosen_histories_num}")
    write_chosen_info(output_json_file, f"All chosen histories: {all_chosen_histories_num}.")

if __name__ == "__main__":
    args = parser.parse_args()
    # TODO remove the arguments; instead, all experiments should just use the same default location of these files (as defined in README.md)
    main(args.results_parent_folder, args.output_json_file)