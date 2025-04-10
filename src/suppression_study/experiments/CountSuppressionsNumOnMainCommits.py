from multiprocessing import Pool, cpu_count
import os
from os.path import join
from suppression_study.experiments.Experiment import Experiment
from suppression_study.suppression.GrepSuppressionPython import GrepSuppressionPython
from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class CountOfSuppressionsNumOnMainCommits(Experiment):
    """
    Experiment that run GrepSuppressionPython on all commits. 
    Get suppressions in given repositories, and get a csv file which 
    show the number of suppressions in every commit.
    """

    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()
        self.checkout_latest_commits()

        args_for_all_repos = []
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            commit_list_file = join("data", "results", repo_name, "commit_id_list.csv") # only main branch
            if not os.path.exists(commit_list_file):
                write_commit_info_to_csv(repo_dir, commit_list_file)
            print(f"Computed commit list for {repo_name}.")

            dest_dir = join("data", "results", repo_name, "main_commits_suppression_pylint")
            args = [repo_dir, commit_list_file, dest_dir, "pylint"]
            args_for_all_repos.append(args)
            
        # find suppression for all commits, in parallel on different repos
        cores_to_use = cpu_count() - 1 # leave one core for other processes
        print(f"Using {cores_to_use} cores to find repositories in parallel.")
        with Pool(processes=cores_to_use) as pool:
            pool.map(suppression_wrapper, args_for_all_repos)

def suppression_wrapper(args):
    print(f"Starting get suppressions on {args[0]}")
    GrepSuppressionPython(*args).grep_suppression_for_all_commits()
    print(f"Done with getting suppressions on {args[0]}")


if __name__ == "__main__":
    CountOfSuppressionsNumOnMainCommits().run()