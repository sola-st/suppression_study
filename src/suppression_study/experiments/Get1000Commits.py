import datetime
from os.path import join
from multiprocessing import Pool, cpu_count
from suppression_study.evolution.Select1000Commits import select_1000_commits
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class Get1000Commits(Experiment):
    """
    Get 1000 commits for all repositories.
    """

    def _compute_commit_id_list(self, repo_dir, repo_name):
        repo_name = repo_dir_to_name(repo_dir)
        commit_list_file = join("data", "results", repo_name, "commit_id_list.csv")
        write_commit_info_to_csv(repo_dir, commit_list_file)
        return commit_list_file # all commits

    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()
        self.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        # compute commits to consider list and prepare args for running ExtractHistory in parallel
        args_for_all_repos = []
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            commit_list_file = self._compute_commit_id_list(repo_dir, repo_name)
            print(f"Computed commit list for {repo_name}.")

            output_commit_list_file = commit_list_file.replace(".csv", "_1000.csv")
            args = [repo_dir, commit_list_file, output_commit_list_file]
            args_for_all_repos.append(args)
            
        # start selecting 1000 commits, in parallel on different repos
        cores_to_use = cpu_count() - 1 # leave one core for other processes
        print(f"Using {cores_to_use} cores to get 1000 commits in parallel.")
        start_time = datetime.datetime.now()
        with Pool(processes=cores_to_use) as pool:
            pool.map(select_commits_wrapper, args_for_all_repos)
        end_time = datetime.datetime.now()
        executing_time = (end_time - start_time).seconds
        print(f"Totally executing time: {executing_time} seconds")

def select_commits_wrapper(args):
    print(f"Starting selecting 1000 commits on {args[0]}")
    select_1000_commits(*args)
    print(f"Done with commits selection on {args[0]}")

if __name__ == "__main__":
    Get1000Commits().run()