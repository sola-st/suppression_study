from os.path import join
from collections import Counter
import matplotlib.pyplot as plt
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name
from suppression_study.warnings.WarningSuppressionUtil import read_mapping_from_csv


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

    def _compute_suppression_to_warnings(self, repo_dir_to_pairs):
        all_pairs = []
        for _, pairs in repo_dir_to_pairs.items():
            all_pairs.extend(pairs)

        suppression_to_warnings = {}
        for pair in all_pairs:
            suppression, warning = pair
            warnings = suppression_to_warnings.get(suppression, [])
            if warning is not None:
                warnings.append(warning)
            suppression_to_warnings[suppression] = warnings
        return suppression_to_warnings

    def plot_suppression_to_warnings_distribution(self, suppression_to_warnings):
        nb_warnings_to_occurrences = Counter()
        for _, warnings in suppression_to_warnings.items():
            nb_warnings_to_occurrences[len(warnings)] += 1

        print(nb_warnings_to_occurrences)
        x_to_y = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5--10": 0, ">10": 0}
        for nb_warnings, occurrences in nb_warnings_to_occurrences.items():
            if nb_warnings in range(5):
                x_to_y[str(nb_warnings)] = occurrences
            elif 5 <= nb_warnings <= 10:
                x_to_y["5--10"] += occurrences
            else:
                x_to_y[">10"] += occurrences

        output_file = join("data", "results", "suppression_to_warnings.pdf")
        plt.bar(x_to_y.keys(), x_to_y.values())
        plt.xlabel("Warnings suppressed by a suppression")
        plt.ylabel("Occurrences")
        plt.tight_layout()
        plt.savefig(output_file)
        print(f"Saved histogram to {output_file}")

    def run(self):
        # prepare repos
        self.get_repo_dirs()
        repo_dir_to_commit = self.checkout_latest_commits()

        repo_dir_to_pairs = self._read_mapping_results(repo_dir_to_commit)
        suppression_to_warnings = self._compute_suppression_to_warnings(
            repo_dir_to_pairs)
        self.plot_suppression_to_warnings_distribution(suppression_to_warnings)


if __name__ == "__main__":
    VisualizeWarningSuppressionMapsOnLatestCommit().run()
