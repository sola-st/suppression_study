from os.path import join
from suppression_study.experiments.Experiment import Experiment
from suppression_study.evolution.ExtractHistory import main as extract_history
from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class ComputeSuppressionHistories(Experiment):
    """
    Computes the suppression histories of all repositories.
    """

    def _compute_commit_id_list(self, repo_dir, repo_name):
        repo_name = repo_dir_to_name(repo_dir)
        commit_list_file = join(
            "data", "results", repo_name, "commit_id_list.csv")
        write_commit_info_to_csv(
            repo_dir, commit_list_file, oldest_n_commits=5)  # TODO change to 1000
        return commit_list_file

    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()
        print(f"Found {len(repo_dirs)} repositories.")

        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            commit_list_file = self._compute_commit_id_list(repo_dir, repo_name)
            print(f"Computed commit list for {repo_name}.")
            dest_dir = join("data", "results", repo_name)
            print(f"Extracting suppression histories for {repo_name}.")
            extract_history(repo_dir, commit_list_file, dest_dir)


if __name__ == "__main__":
    ComputeSuppressionHistories().run()
