import csv
import json
import subprocess
from datetime import datetime
from os.path import join
from datetime import datetime


def get_commit_info(commit_hash, project_dir):
    """Get authors and date information for a given commit hash in a specific repo."""
    # Command to get the commit author and co-authors
    author_command = f"git -C {project_dir} log --format='%aN' {commit_hash} -n 1"
    coauthor_command = f"git -C {project_dir} log --format='%b' {commit_hash} -n 1"
    # Command to get the commit date
    date_command = f"git -C {project_dir} log --format='%ai' {commit_hash} -n 1"

    author = subprocess.check_output(author_command, shell=True).decode('utf-8').strip()
    coauthor_output = subprocess.check_output(coauthor_command, shell=True).decode('utf-8').strip()
    commit_date = subprocess.check_output(date_command, shell=True).decode('utf-8').strip()

    # Find any Co-authored-by: lines in the commit body
    coauthors = []
    for line in coauthor_output.split('\n'):
        if line.startswith('Co-authored-by:'):
            coauthor_name = line.split(':', 1)[1].strip().split('<')[0].strip()
            coauthors.append(coauthor_name)

    # Combine author and co-authors into a single list
    authors = [author] + coauthors

    return authors, commit_date

def calculate_date_difference(date1, date2):
    """Calculate the difference in days between two dates."""
    delta = date2 - date1
    return delta.days

def main(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    results = []
    for check_item in data:
        url =  check_item["Check"][0]
        repo_name = url.split("/")[-3]
        repo_path = join("data", "repos", repo_name)

        check_dict = check_item["Check"][1]
        previous_commit = check_dict["previous_commit"]
        commit = check_dict["commit"]

        authors1, date1 = get_commit_info(previous_commit, repo_path)
        authors2, date2 = get_commit_info(commit, repo_path)

        # Check authors and calculate date difference
        author = None
        delta_days = None
        if authors1 and authors2:
            if authors1 == authors2:
                author = "same"
            elif set(authors1) & set(authors2):
                author = "different but inclusive"
            else:
                author = "different"

        if date1 and date2:
            date1 = date1.split()[0]  # Extract only the date part (ignoring time)
            date2 = date2.split()[0]
            date_format = "%Y-%m-%d"
            delta_days = (datetime.strptime(date2, date_format) - datetime.strptime(date1, date_format)).days

        results.append([previous_commit, ', '.join(authors1), date1, commit, ', '.join(authors2), date2, author, delta_days])

    with open(join("data", "results", "inspection_author_time3.csv"), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(results)


if __name__ == "__main__":
    file_path = join("data", "results", "inspection_accidental_commits.json")
    main(file_path)

