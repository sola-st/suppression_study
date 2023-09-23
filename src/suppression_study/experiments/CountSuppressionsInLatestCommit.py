from os.path import join, getsize
from os import makedirs
from tempfile import TemporaryDirectory
from shutil import move
from suppression_study.experiments.Experiment import Experiment
from suppression_study.suppression.GrepSuppressionPython import GrepSuppressionPython
from suppression_study.suppression.Suppression import read_suppressions_from_file
from suppression_study.utils.LaTeXUtils import LaTeXTable
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class CountSuppressionsInLatestCommit(Experiment):
    def _find_suppressions(self, repo_dir, commit):
        with TemporaryDirectory() as tmp_dir:
            print(
                f"Grepping for suppressions in {repo_dir} at commit {commit}")

            # run grep to find suppression in the latest commit
            grep = GrepSuppressionPython(repo_dir, commit, tmp_dir, checker="pylint")
            grep.grep_suppression_for_specific_commit()
            tmp_out_file = join(tmp_dir, f"{commit}_suppression.csv")

            # move result file to expected location
            repo_name = repo_dir_to_name(repo_dir)
            output_dir = join("data", "results",
                              repo_name, "commits", commit)
            makedirs(output_dir, exist_ok=True)
            out_file = join(output_dir, "suppressions.csv")
            move(tmp_out_file, out_file)

            if getsize(out_file) == 0:
                print(
                    f"WARNING: no suppressions found in {repo_dir} at commit {commit}")

            return out_file

    def _produce_result_table(self, repo_dir_to_out_file):
        table = LaTeXTable(["Project", "Suppressions"])
        total_suppressions = 0
        for repo_dir, out_file in repo_dir_to_out_file.items():
            suppressions = read_suppressions_from_file(out_file)
            print(f"Found {len(suppressions)} suppressions in {out_file}")
            repo_name = repo_dir_to_name(repo_dir)
            table.add_row([repo_name, len(suppressions)])
            total_suppressions += len(suppressions)
        table.add_separator()
        table.add_row(["Total", "{:,}".format(total_suppressions)])

        latex_out_file = join("data", "results", "suppressions_per_repo.tex")
        with open(latex_out_file, "w") as f:
            f.write(table.to_latex())
        print(f"Result table written to {latex_out_file}")

    def run(self):
        # prepare repositories
        self.get_repo_dirs()
        repo_dir_to_commit = self.checkout_latest_commits()

        # find suppressions
        repo_dir_to_out_file = {}
        for repo_dir, commit in repo_dir_to_commit.items():
            out_file = self._find_suppressions(repo_dir, commit)
            repo_dir_to_out_file[repo_dir] = out_file

        # produce result table
        self._produce_result_table(repo_dir_to_out_file)


if __name__ == "__main__":
    CountSuppressionsInLatestCommit().run()
