from os.path import join, exists
from os import makedirs
from tempfile import TemporaryDirectory
from shutil import move
import subprocess
import re
import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr
from suppression_study.experiments.Experiment import Experiment
from suppression_study.suppression.GrepSuppressionPython import GrepSuppressionPython
from suppression_study.suppression.Suppression import read_suppressions_from_file
from suppression_study.utils.LaTeXUtils import LaTeXTable
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class CountSuppressionsOnLatestCommit(Experiment):
    def _count_suppressions(self, repo_dir, commit):
        with TemporaryDirectory() as tmp_dir:
            print(
                f"Grepping for suppressions in {repo_dir} at commit {commit}")

            # run grep to find suppression in the latest commit
            grep = GrepSuppressionPython(
                repo_dir, commit, tmp_dir, checker="pylint")
            grep.grep_suppression_for_specific_commit()
            tmp_out_file = join(tmp_dir, f"{commit}_suppression.csv")

            # move result file to expected location
            repo_name = repo_dir_to_name(repo_dir)
            output_dir = join("data", "results",
                              repo_name, "commits", commit)
            makedirs(output_dir, exist_ok=True)
            out_file = join(output_dir, "suppressions.csv")
            if not exists(tmp_out_file):
                print(
                    f"WARNING: no suppressions found in {repo_dir} at commit {commit}")
                # create an empty file to indicate that no suppressions were found
                open(tmp_out_file, 'a').close()
            move(tmp_out_file, out_file)

            # count suppressions
            suppressions = read_suppressions_from_file(out_file)
            print(f"Found {len(suppressions)} suppressions in {out_file}")

            return len(suppressions)

    def _count_lines_of_code(self, repo_dir):
        command_line = f"sloccount {repo_dir}"
        result = subprocess.run(command_line, shell=True,
                                stdout=subprocess.PIPE, universal_newlines=True)
        out_lines = result.stdout.split("\n")
        python_out_lines = [l for l in out_lines if l.startswith("python:")]
        assert len(python_out_lines) == 1
        m = re.match(r"python: +(\d+) \(.*", python_out_lines[0])
        loc = int(m.groups()[0])
        return loc

    def _count_python_files(self, repo_dir):
        command_line = f"find {repo_dir} -name '*.py' | wc -l"
        result = subprocess.run(command_line, shell=True,
                                stdout=subprocess.PIPE, universal_newlines=True)
        return int(result.stdout.strip())

    def _produce_result_table(self, repo_dir_to_suppressions, repo_dir_to_loc, repo_dir_to_python_files):
        table = LaTeXTable(["Project",
                            "Python files",
                            "LoC (Python)",
                            "Suppressions",
                            "Suppr./file",
                            "Suppr./KLoC"])
        total_suppressions = 0
        total_loc = 0
        total_files = 0
        for repo_dir, nb_suppressions in repo_dir_to_suppressions.items():
            loc = repo_dir_to_loc[repo_dir]
            nb_files = repo_dir_to_python_files[repo_dir]
            repo_name = repo_dir_to_name(repo_dir)
            table.add_row([repo_name,
                           "{:,}".format(nb_files),
                           "{:,}".format(loc),
                           "{:,}".format(nb_suppressions),
                           round(nb_suppressions/nb_files, 2),
                           round(1000*nb_suppressions/loc, 2)])
            total_suppressions += nb_suppressions
            total_loc += loc
            total_files += nb_files
        table.add_separator()
        table.add_row(["Total",
                       "{:,}".format(total_files),
                       "{:,}".format(total_loc),
                       "{:,}".format(total_suppressions),
                       round(total_suppressions/total_files, 2),
                       round(1000*total_suppressions/total_loc, 2)])

        latex_out_file = join("data", "results", "suppressions_per_repo.tex")
        with open(latex_out_file, "w") as f:
            f.write(table.to_latex())
        print(f"Result table written to {latex_out_file}")

    def _plot_suppressions_over_loc(self, repo_dir_to_suppressions, repo_dir_to_loc):
        xs = []
        ys = []
        for repo_dir, nb_suppressions in repo_dir_to_suppressions.items():
            loc = repo_dir_to_loc[repo_dir]
            xs.append(loc)
            ys.append(nb_suppressions)

        plt.xscale("log")
        plt.yscale("log")
        plt.scatter(xs, ys)
        plt.xlabel("Lines of code (Python)")
        plt.ylabel("Nb. of suppressions")
        plt.tight_layout()
        output_file = join("data", "results", "suppressions_over_loc.pdf")
        plt.savefig(output_file)
        print(f"Saved histogram to {output_file}")

        correlation = pearsonr(xs, ys)
        print(
            f"Pearson correlation coefficient (suppressions vs. LoC): {correlation[0]}")

    def run(self):
        # prepare repositories
        self.get_repo_dirs()
        repo_dir_to_commit = self.checkout_latest_commits()

        # find and count suppressions
        repo_dir_to_suppressions = {}
        for repo_dir, commit in repo_dir_to_commit.items():
            nb_suppressions = self._count_suppressions(repo_dir, commit)
            repo_dir_to_suppressions[repo_dir] = nb_suppressions

        # count lines of code
        repo_dir_to_loc = {}
        for repo_dir in repo_dir_to_commit.keys():
            loc = self._count_lines_of_code(repo_dir)
            repo_dir_to_loc[repo_dir] = loc

        # count Python files
        repo_dir_to_python_files = {}
        for repo_dir in repo_dir_to_commit.keys():
            nb_files = self._count_python_files(repo_dir)
            repo_dir_to_python_files[repo_dir] = nb_files

        # produce result table
        self._produce_result_table(
            repo_dir_to_suppressions, repo_dir_to_loc, repo_dir_to_python_files)

        # plot nb of suppressions vs LoC
        self._plot_suppressions_over_loc(
            repo_dir_to_suppressions, repo_dir_to_loc)


if __name__ == "__main__":
    exp = CountSuppressionsOnLatestCommit()
    exp.repo_file = join("data", "python_repos_46_using_pylint.txt")
    exp.run()
