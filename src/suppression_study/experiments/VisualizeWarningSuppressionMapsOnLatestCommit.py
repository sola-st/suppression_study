from os.path import join
from collections import Counter
import matplotlib.pyplot as plt
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name
from suppression_study.warnings.WarningSuppressionUtil import read_mapping_from_csv
from suppression_study.warnings.Warning import read_warning_from_file
from suppression_study.suppression.Suppression import read_suppressions_from_file
from suppression_study.utils.LaTeXUtils import LaTeXTable


class VisualizeWarningSuppressionMapsOnLatestCommit(Experiment):
    """
    Experiment that creates plots etc. to visualize the warning suppression maps.

    Depends on:
      * ComputeWarningSuppressionMapsOnLatestCommit
    """

    def _read_mapping_results(self, repo_dir_to_commit):
        repo_dir_to_mapping = {}

        # TODO add mypy support
        checker = "pylint"

        for repo_dir, commit in repo_dir_to_commit.items():
            repo_name = repo_dir_to_name(repo_dir)
            mapping_file = join("data", "results", repo_name,
                                "commits", commit, f"{checker}_mapping.csv")
            suppression_warning_pairs = read_mapping_from_csv(
                file=mapping_file)
            repo_dir_to_mapping[repo_dir] = suppression_warning_pairs

        return repo_dir_to_mapping

    def _compute_one_to_many_maps(self, repo_dir_to_pairs):
        all_pairs = []
        for _, pairs in repo_dir_to_pairs.items():
            all_pairs.extend(pairs)

        suppression_to_warnings = {}  # maps each suppression to all warnings it suppresses
        warning_to_suppressions = {}  # maps each warning to all suppressions that suppress it
        for pair in all_pairs:
            suppression, warning = pair

            # update suppression_to_warnings
            warnings = suppression_to_warnings.get(suppression, [])
            if warning is not None:
                warnings.append(warning)
            suppression_to_warnings[suppression] = warnings

            # update warning_to_suppressions
            if warning is not None:
                suppressions = warning_to_suppressions.get(warning, [])
                suppressions.append(suppression)
                warning_to_suppressions[warning] = suppressions

        return suppression_to_warnings, warning_to_suppressions

    def _plot_one_to_many_distribution(self, x_to_ys, xlabel, ylabel, outfile):
        nb_ys_to_occurrences = Counter()
        for _, warnings in x_to_ys.items():
            nb_ys_to_occurrences[len(warnings)] += 1

        print(nb_ys_to_occurrences)
        x_to_y = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5--10": 0, ">10": 0}
        for nb_warnings, occurrences in nb_ys_to_occurrences.items():
            if nb_warnings in range(5):
                x_to_y[str(nb_warnings)] = occurrences
            elif 5 <= nb_warnings <= 10:
                x_to_y["5--10"] += occurrences
            else:
                x_to_y[">10"] += occurrences

        output_file = join("data", "results", outfile)
        plt.clf()
        plt.bar(x_to_y.keys(), x_to_y.values())
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.tight_layout()
        plt.savefig(output_file)
        print(f"Saved histogram to {output_file}")

    def _load_useless_suppression(self, repo_name, checker, commit):
        useless_suppressions_file = join("data", "results", repo_name,
                                         "commits", commit, f"{checker}_useless_suppressions.csv")
        useless_suppressions = read_suppressions_from_file(
            useless_suppressions_file)
        return useless_suppressions

    def _load_useful_suppression(self, repo_name, checker, commit):
        useful_suppressions_file = join("data", "results", repo_name,
                                        "commits", commit, f"{checker}_useful_suppressions.csv")
        useful_suppressions = read_suppressions_from_file(
            useful_suppressions_file)
        return useful_suppressions

    def _compute_useful_and_useless_suppressions_table(self, repo_dir_to_commit):
        # TODO add mypy support
        checker = "pylint"

        table = LaTeXTable(
            column_names=["Project", "Useful suppressions", "Useless suppressions"])
        total_useless_suppressions = 0
        total_useful_suppressions = 0
        for repo_dir, commit in repo_dir_to_commit.items():
            repo_name = repo_dir_to_name(repo_dir)

            useful_suppressions = self._load_useful_suppression(
                repo_name, checker, commit)
            total_useful_suppressions += len(useful_suppressions)
            useless_suppressions = self._load_useless_suppression(
                repo_name, checker, commit)
            total_useless_suppressions += len(useless_suppressions)

            table.add_row([repo_name,
                           "{:,}".format(len(useful_suppressions)),
                           "{:,}".format(len(useless_suppressions))])

        table.add_separator()
        table.add_row(["Total",
                       "{:,}".format(total_useful_suppressions),
                       "{:,}".format(total_useless_suppressions)])

        latex_out_file = join(
            "data", "results", "useless_and_useful_suppressions.tex")
        with open(latex_out_file, "w") as f:
            f.write(table.to_latex())
        print(f"Result table written to {latex_out_file}")

    def _compute_suppression_and_unsuppressed_warnings_table(self, repo_dir_to_commit):
        # TODO add mypy support
        checker = "pylint"

        warning_counts = {
            "Suppressed": [],
            "Unsuppressed": []
        }
        repo_names = []
        for repo_dir, commit in repo_dir_to_commit.items():
            repo_name = repo_dir_to_name(repo_dir)
            repo_names.append(repo_name)

            warnings_file = join("data", "results", repo_name,
                                 "commits", commit, f"{checker}_warnings.csv")
            unsuppressed_warnings = read_warning_from_file(warnings_file)
            suppressed_warnings_file = join("data", "results", repo_name,
                                            "commits", commit, f"{checker}_suppressed_warnings.csv")
            suppressed_warnings = read_warning_from_file(
                suppressed_warnings_file)

            print(
                f"{repo_name}, suppressed: {len(suppressed_warnings)}, unsuppressed: {len(unsuppressed_warnings)}")

            warning_counts["Suppressed"].append(len(suppressed_warnings))
            warning_counts["Unsuppressed"].append(len(unsuppressed_warnings))

        output_file = join("data", "results",
                           "suppressed_vs_unsuppressed_warnings.pdf")
        plt.clf()
        bottom = [0] * len(repo_names)
        for label, counts in warning_counts.items():
            plt.bar(repo_names, counts, label=label, bottom=bottom)
        plt.xlabel("Projects")
        plt.ylabel("Number of warnings")
        plt.tight_layout()
        plt.savefig(output_file)
        print(f"Saved histogram to {output_file}")

    def _suppressions_to_kind_counter(self, suppressions):
        kinds = []
        for s in suppressions:
            kinds.extend(s.get_short_names())
        kind_to_count = Counter(kinds)
        return kind_to_count

    def _table_with_kinds_of_suppressions(self, repo_dir_to_commit):
        # TODO add mypy support
        checker = "pylint"

        all_useful = []
        all_useless = []
        for repo_dir, commit in repo_dir_to_commit.items():
            repo_name = repo_dir_to_name(repo_dir)
            useful_suppressions = self._load_useful_suppression(
                repo_name, checker, commit)
            all_useful.extend(useful_suppressions)
            useless_suppressions = self._load_useless_suppression(
                repo_name, checker, commit)
            all_useless.extend(useless_suppressions)

        useful_kinds = self._suppressions_to_kind_counter(
            all_useful)
        useless_kinds = self._suppressions_to_kind_counter(
            all_useless)

        top_10_useful = useful_kinds.most_common(10)
        top_10_useless = useless_kinds.most_common(10)
        table = LaTeXTable(column_names=["Rank", "Useful", "Useless"])
        for i in range(10):
            useful_kind, useful_count = top_10_useful[i]
            useless_kind, useless_count = top_10_useless[i]
            table.add_row([i+1,
                           f"{useful_kind} ({useful_count})",
                           f"{useless_kind} ({useless_count})"])
        outfile = join("data", "results",
                       "useful_and_useless_suppressions.tex")
        with open(outfile, "w") as f:
            f.write(table.to_latex())
        print(f"Result table written to {outfile}")

    def run(self):
        # prepare repos
        self.get_repo_dirs()
        repo_dir_to_commit = self.checkout_latest_commits()

        # create plots that show how many warnings are suppressed by a single suppression and vice versa
        repo_dir_to_pairs = self._read_mapping_results(repo_dir_to_commit)
        suppression_to_warnings, warning_to_suppressions = self._compute_one_to_many_maps(
            repo_dir_to_pairs)
        self._plot_one_to_many_distribution(suppression_to_warnings,
                                            xlabel="Suppressions that suppress a single warning",
                                            ylabel="Occurrences",
                                            outfile="warning_to_suppressions.pdf")
        self._plot_one_to_many_distribution(warning_to_suppressions,
                                            xlabel="Warnings suppressed by a single suppression",
                                            ylabel="Occurrences",
                                            outfile="suppression_to_warnings.pdf")

        # table of useless and useful suppressions per project
        self._compute_useful_and_useless_suppressions_table(repo_dir_to_commit)

        # table of suppressed and unsuppressed warnings per project
        self._compute_suppression_and_unsuppressed_warnings_table(
            repo_dir_to_commit)

        # show kinds of useless and useful suppressions
        self._table_with_kinds_of_suppressions(repo_dir_to_commit)


if __name__ == "__main__":
    VisualizeWarningSuppressionMapsOnLatestCommit().run()
