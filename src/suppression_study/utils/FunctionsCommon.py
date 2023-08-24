import subprocess

class FunctionsCommon():
    
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
    
    def get_commit_csv(repo_dir, commit_id_csv):
        # Get commit file
        '''
        Valid for the repository which the repo_dir point to is the latest commit status,
        otherwise, will miss to get all commits. --> useful on running tests.
        Here, the oldest commits locates the 1st line of the csv file. (with option --reverse)
        '''
        commit_command = "git log --pretty=format:'\"%h\",\"%cd\"' --abbrev=8" 
        git_get_commits = subprocess.run(commit_command, cwd=repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        commits = git_get_commits.stdout 

        with open(commit_id_csv, "w") as f:
            f.writelines(commits)

    def get_commit_date_lists_future_version(repo_dir):
        '''
        Valid for the repository which the repo_dir point to is the latest commit status,
        otherwise, will miss to get all commits. --> useful on running tests.
        Here, the oldest commits locates the 1st line of the csv file. (with option --reverse)
        '''
        commit_command = "git log --pretty=format:'\"%h\",\"%cd\"' --abbrev=8" 
        git_get_commits = subprocess.run(commit_command, cwd=repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        commits_dates = git_get_commits.stdout 

        all_commits = []
        all_dates = []
        for line in commits_dates:
            tmp = line.split(",")
            all_commits.append(tmp[0])
            all_dates.append(tmp[1])

        return all_commits, all_dates
