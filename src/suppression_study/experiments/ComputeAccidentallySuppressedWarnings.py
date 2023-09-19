from os.path import join
from os.path import exists
from suppression_study.experiments.Experiment import Experiment
from suppression_study.evolution.AccidentallySuppressedWarning import main as find_accidentally_suppressed_warnings
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class ComputeAccidentallySuppressedWarnings(Experiment):
    """
    Applies the AccidentalSuppressionFinder to the the first 1000 commits of each repository.

    Depends on:
     * ComputeSuppressionHistories
    """
    
    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()

        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            print(f"Computing accidentally suppressed warnings for {repo_name}")
            commits_file = join("data", "results", repo_name, "commit_id_list.csv")
            assert exists(commits_file)
            history_file = join("data", "results", repo_name, "gitlog_history" "histories_suppression_level_all.json")
            assert exists(history_file)
            results_dir = join("data", "results", repo_name)
            find_accidentally_suppressed_warnings(repo_dir, commits_file, history_file, results_dir)


if __name__ == "__main__":
    ComputeAccidentallySuppressedWarnings().run()