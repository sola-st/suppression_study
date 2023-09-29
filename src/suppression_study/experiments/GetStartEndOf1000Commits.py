import os
from suppression_study.experiments.Experiment import Experiment
from os.path import join

from suppression_study.utils.FunctionsCommon import get_commit_list
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class GetStartEndOf1000Commits(Experiment):

    def get_start_end_1000_commits(self, repo_name, all_commits_all_branches_csv, selected_1000_csv, start_end_commits_1000_csv):
        '''
        Focus on commits on only main branch, the commits can be discontinuous.
        eg,. commit 1 and commit 2 on main branch can skip the commits in side branches 
            in the middle of commit 1 and 2.
        This function is designed to get the start and end commits of the selected 1000 commits.
        Return a file that records the commit hashes and indexes of the start and end commits.
        '''
        all_commits_all_branches = get_commit_list(all_commits_all_branches_csv) # start from latest
        all_commits_all_branches.reverse()
        selected_1000_commits = get_commit_list(selected_1000_csv) # start from latest
        start_commit = selected_1000_commits[-1]
        start_commit_index = all_commits_all_branches.index(start_commit)
        end_commit = selected_1000_commits[0]
        end_commit_index = all_commits_all_branches.index(end_commit)

        with open(join(start_end_commits_1000_csv), "a") as f:
            f.write(f"{repo_name},{start_commit},{start_commit_index},{end_commit},{end_commit_index}\n")


    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()

        # prepare start and end commit information
        start_end_commits_1000_csv = join("data", "results", "start_end_commits_1000.csv")
        if not os.path.exists(start_end_commits_1000_csv):
            for repo_dir in repo_dirs:
                repo_name = repo_dir_to_name(repo_dir)
                common_folder = join("data", "results", repo_name)
                all_commits_all_branches_csv = join(common_folder, "commit_id_list_all_branches.csv")
                selected_1000_csv = join(common_folder, "commit_id_list_1000.csv")
                self.get_start_end_1000_commits(repo_name, all_commits_all_branches_csv, 
                        selected_1000_csv, start_end_commits_1000_csv)
                print(f"Computed start and end commit for {repo_name}.")

if __name__ == "__main__":
    GetStartEndOf1000Commits().run()
    