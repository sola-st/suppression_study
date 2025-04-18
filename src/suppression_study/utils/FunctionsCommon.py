import subprocess
from os import makedirs
from os.path import dirname
    
def get_commit_list(commit_id_csv):
    '''Read given commit .csv file, return a commit list'''
    all_commits = []
    with open(commit_id_csv, "r") as f: # 2 columns: commit and date
        line = f.readline()
        while line:
            tmp =  line.split(",")
            commit = tmp[0].replace("\"", "").strip()
            all_commits.append(commit)
            line = f.readline()
    return all_commits
    
def get_commit_date_lists(commit_id_csv):
    '''Read given commit .csv file, return a commit list and a date list'''
    all_commits = []
    all_dates = []
    with open(commit_id_csv, "r") as f: # 2 columns: commit and date
        line = f.readline()
        while line:
            tmp =  line.split(",")
            commit = tmp[0].replace("\"", "").strip()
            all_commits.append(commit)

            date = tmp[1].replace("\"", "").strip()
            all_dates.append(date)
            
            line = f.readline()
    return all_commits, all_dates
    
def write_commit_info_to_csv(repo_dir, commit_id_csv, oldest_n_commits=None):
    '''
    Valid for the repository which the repo_dir point to is the latest commit status,
    otherwise, will miss to get all commits. --> useful on running tests.
    The newest commits will be the 1st line of the csv file.
    '''
    commit_command = "git log --pretty=format:'\"%h\",\"%cd\"' --abbrev=8 --first-parent" 
    git_get_commits = subprocess.run(commit_command, cwd=repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    commits = git_get_commits.stdout 

    if oldest_n_commits is not None:
        commits = "\n".join(commits.split("\n")[-oldest_n_commits:])

    makedirs(dirname(commit_id_csv), exist_ok=True)
    with open(commit_id_csv, "w") as f:
        f.writelines(commits)

