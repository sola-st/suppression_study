from os.path import join
from shutil import move
from tempfile import TemporaryDirectory
from suppression_study.experiments.Experiment import Experiment
from suppression_study.warnings.WarningSuppressionMapper import main as warning_suppression_mapper
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class ComputeWarningSuppressionMapsOnLatestCommit(Experiment):
    """
    Applies the WarningSuppressionMapper to the latest commit of each repository,
    where "latest" is is the latest we consider in the study.

    Depends on:
     * CountSuppressionsOnLatestCommit
     * RunCheckersOnLatestCommit
    """

    def _run_for_checker(self, checker, repo_dir, commit):
        repo_name = repo_dir_to_name(repo_dir)
        commit_dir = join("data", "results", repo_name, "commits", commit)
        suppressions_file = join(commit_dir, "suppressions.csv")
        warnings_file = join(commit_dir, f"{checker}_warnings.csv")

        with TemporaryDirectory() as tmp_results_dir:
            warning_suppression_mapper(
                repo_dir, commit, checker, tmp_results_dir, suppressions_file, warnings_file)

            move(join(tmp_results_dir, f"{commit}_mapping.csv"), join(
                commit_dir, f"{checker}_mapping.csv"))
            move(join(tmp_results_dir, f"{commit}_suppressed_warnings.csv"), join(
                commit_dir, f"{checker}_suppressed_warnings.csv"))
            move(join(tmp_results_dir, f"{commit}_useless_suppressions.csv"), join(
                commit_dir, f"{checker}_useless_suppressions.csv"))
            move(join(tmp_results_dir, f"{commit}_useful_suppressions.csv"), join(
                commit_dir, f"{checker}_useful_suppressions.csv"))
            print(f"Moved results into {commit_dir}/{checker}_*.csv")

    def run(self):
        # prepare repositories
        self.get_repo_dirs()
        repo_dir_to_commit = self.checkout_latest_commits()

        for repo_dir, commit in repo_dir_to_commit.items():
            for checker in ["mypy", "pylint"]:
                print(
                    f"Computing warning suppression map for {repo_dir} at commit {commit} with checker {checker}")
                self._run_for_checker(checker, repo_dir, commit)


if __name__ == "__main__":
    ComputeWarningSuppressionMapsOnLatestCommit().run()
