from os.path import join, normpath
from os import sep
from os import makedirs
from tempfile import TemporaryDirectory
from shutil import move
from suppression_study.experiments.Experiment import Experiment
from suppression_study.suppression.GrepSuppressionPython import GrepSuppressionPython


class CountSuppressionsInLatestCommit(Experiment):
    def run(self):
        self.get_repo_dirs()
        repo_dir_to_commit = self.checkout_latest_commits()

        for repo_dir, commit in repo_dir_to_commit.items():
            with TemporaryDirectory() as tmp_dir:
                print(
                    f"Grepping for suppressions in {repo_dir} at commit {commit}")

                # run grep to find suppression in the latest commit
                grep = GrepSuppressionPython(repo_dir, commit, tmp_dir)
                grep.grep_suppression_for_specific_commit()
                tmp_out_file = join(tmp_dir, f"{commit}_suppression.csv")

                # move result file to expected location
                # TODO: perhaps we should adapt GrepSuppressionPython to write to the expected location directly
                repo_name = normpath(repo_dir).split(sep)[-1]
                output_dir = join("data", "results",
                                  repo_name, "commits", commit)
                makedirs(output_dir, exist_ok=True)
                move(tmp_out_file, join(output_dir, "suppressions.csv"))


if __name__ == "__main__":
    CountSuppressionsInLatestCommit().run()
