from os import makedirs
from os.path import join
from shutil import move
from tempfile import TemporaryDirectory
from suppression_study.experiments.Experiment import Experiment
from suppression_study.suppression.GrepSuppressionPython import GrepSuppressionPython
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class FindSuppressionsOnLatestCommit(Experiment):
    """
    Greps for pylint and mypy suppressions on the latest commit
    of the project, where "latest" means the commit we've set as
    the latest to consider in the study.
    """

    def run(self):
        # prepare repositories
        self.get_repo_dirs()
        repo_dir_to_commit_id = self.checkout_latest_commits()

        for repo_dir, commit_id in repo_dir_to_commit_id.items():
            print(f"Finding suppressions on {repo_dir} at {commit_id}")
            repo_name = repo_dir_to_name(repo_dir)
            with TemporaryDirectory() as tmp_results_dir:
                grep = GrepSuppressionPython(
                    repo_dir, commit_id, tmp_results_dir)
                grep.grep_suppression_for_specific_commit()
                tmp_result_file = join(
                    tmp_results_dir, f"{commit_id}_suppression.csv")
                target_dir = join("data", "results", repo_name,
                                   "commits", commit_id)
                target_file = join(target_dir, f"suppressions.csv")
                makedirs(target_dir, exist_ok=True)
                move(tmp_result_file, target_file)
                print(f"Have copied suppressions into {target_file}")


if __name__ == "__main__":
    FindSuppressionsOnLatestCommit().run()
