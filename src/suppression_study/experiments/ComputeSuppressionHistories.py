import os
from os.path import join
from multiprocessing import Pool, cpu_count
from suppression_study.evolution.Select1000Commits import select_1000_commits
from suppression_study.experiments.Experiment import Experiment
from suppression_study.evolution.ExtractHistory import main as extract_history
from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class ComputeSuppressionHistories(Experiment):
    """
    Computes the suppression histories of all repositories.
    """

    def _compute_1000_commit_id_list(self, repo_dir, commit_list_file_1000):
        commit_list_file_1000_all = commit_list_file_1000.replace("_1000", "")
        write_commit_info_to_csv(repo_dir, commit_list_file_1000_all)

        select_1000_commits(repo_dir, commit_list_file_1000)
        return commit_list_file_1000

    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()
        self.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        # compute commits to consider list and prepare args for running ExtractHistory in parallel
        args_for_all_repos = []
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            commit_list_file_1000 = join("data", "results", repo_name, "commit_id_list_1000.csv")
            if not os.path.exists(commit_list_file_1000):
                # Depending on the experiment "Get1000Commits" is done or not
                commit_list_file_1000 = self._compute_1000_commit_id_list(repo_dir, commit_list_file_1000)
            print(f"Computed commit list for {repo_name}.")

            dest_dir = join("data", "results", repo_name)
            args = [repo_dir, commit_list_file_1000, dest_dir]
            args_for_all_repos.append(args)
            
        # extract histories, in parallel on different repos
        cores_to_use = cpu_count() - 1 # leave one core for other processes
        print(f"Using {cores_to_use} cores to extract histories in parallel.")
        with Pool(processes=cores_to_use) as pool:
            pool.map(extract_history_wrapper, args_for_all_repos)

def extract_history_wrapper(args):
    print(f"Starting history extraction on {args[0]}")
    extract_history(*args)
    print(f"Done with history extraction on {args[0]}")

if __name__ == "__main__":
    ComputeSuppressionHistories().run()
