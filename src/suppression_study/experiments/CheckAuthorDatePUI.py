import csv
import json
import subprocess
from datetime import datetime
from os.path import join
from datetime import datetime
from suppression_study.evolution.ExtractHistory import read_histories_from_json


history_dict = {}

def calculate_date_difference(date1, date2):
    """Calculate the difference in days between two dates."""
    delta = date2 - date1
    return delta.days

def read_histories(repo_name):
    if not repo_name in history_dict.keys():
        repo_history_file = join("data", "results", repo_name, "histories_suppression_level_with_chain.json")
        histories = read_histories_from_json(repo_history_file)
        history_dict.update({repo_name : histories})
    
def get_introduce_commit(commit, suppression, repo_name):
    introduce_commit = None
    histories = history_dict[repo_name]
    for h in histories:
        refined_path = ''
        add_event = h[0]
        if add_event.middle_status_chain != "[]":
            if suppression["text"] == add_event.warning_type: 
                if suppression["path"] != add_event.file_path:
                    # this is used to consider file rename
                    refined_path = suppression["path"]
            
                if f"{refined_path}, '{commit}', {suppression['line']}" in str(add_event.middle_status_chain):
                    introduce_commit = add_event.commit_id
                    break
    
    return introduce_commit
            
def get_commit_info(commit_hash, repo_dir):
    """Get authors and date information for a given commit hash in a specific repo."""

    result = subprocess.run(
            ['git', 'show', '--no-patch', '--format="%an|%ad"', commit_hash], 
            capture_output=True, text=True, check=True, cwd=repo_dir)
    output = result.stdout.strip().strip('"')
    author, date_str = output.split('|')
    date = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y %z')
    return author, date

def main(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    results = []
    for check_item in data:
        url =  check_item["Check"][0]
        repo_name = url.split("/")[-3]
        repo_path = join("data", "repos", repo_name)

        check_dict = check_item["Check"][1]
        # previous_commit = check_dict["previous_commit"]
        commit = check_dict["commit"]
        suppression = check_dict["suppression"]
        read_histories(repo_name)
        introduce_commit = get_introduce_commit(commit, suppression, repo_name)

        if introduce_commit:
            author_of_add_commit, date1 = get_commit_info(introduce_commit, repo_path)
            author_of_later_commit, date2 = get_commit_info(commit, repo_path)

            # Check authors and calculate date difference
            author = "different"
            delta_days = None
            if author_of_add_commit and author_of_later_commit:
                if author_of_add_commit == author_of_later_commit:
                    author = "same"
                    
            if date1 and date2:
                delta_days = calculate_date_difference(date1, date2)

            results.append([introduce_commit, author_of_add_commit, date1, commit, author_of_later_commit, date2, author, delta_days])
            introduce_commit = None

    with open(join("data", "results", "inspection_author_time.csv"), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(results)


if __name__ == "__main__":
    file_path = join("data", "results", "inspection_accidental_commits.json")
    main(file_path)

