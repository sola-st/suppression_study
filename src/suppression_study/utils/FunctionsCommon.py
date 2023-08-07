import subprocess
from os.path import join

class FunctionsCommon():
    
    def get_commit_list(commit_id_csv):
        '''Read given commit .csv file, return a commit list'''
        all_commits = []
        with open(commit_id_csv, "r") as f: # 2 columns: commit and date
            line = f.readline()
            while line:
                commit = line.split(",")[0].replace("\"", "").strip()
                all_commits.append(commit)
                line = f.readline()
        return all_commits
    
    def get_commit_csv(repo_dir, commit_id_csv):
        # Get commit file
        '''
        Valid for the repository which the repo_dir point to is in latest commit status,
        otherwise, will miss to get all commits. --> useful on running made-up repository test.
        Here, latest locates the 1st line of the csv file.
        '''
        commit_command = "git log --pretty=format:'\"%h\",\"%cd\"'" 
        git_get_commits = subprocess.run(commit_command, cwd=repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        commits = git_get_commits.stdout 

        with open(commit_id_csv, "w") as f:
            f.writelines(commits)
