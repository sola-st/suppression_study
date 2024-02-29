from typing import List
from os.path import join
import matplotlib.pyplot as plt
from collections import Counter
from suppression_study.experiments.CountSuppressionsOnLatestCommit import CountSuppressionsOnLatestCommit
from suppression_study.suppression.Suppression import Suppression, read_suppressions_from_file
from suppression_study.suppression.NumericSpecificTypeMap import get_warning_kind_to_numeric_code


class DistributionOfSuppressionOnLatestCommit(CountSuppressionsOnLatestCommit):
    """
    Experiment that plots a distribution of the most common
    kinds of problems suppressed by all suppressions in the 
    "latest" commit of the studied repositories.
    """

    def _plot_distribution(self, suppressions: List[Suppression]):
        plt.rcParams.update({'font.size': 13})
        
        kinds = []
        for s in suppressions:
            kinds.extend(s.get_short_names())

        kind_to_count = Counter(kinds)
        output_file = join("data", "results", "suppression_histogram_python.pdf")
        top_kind_to_count = dict(kind_to_count.most_common(10))
        print(top_kind_to_count)
        # set longer bar at the top
        sorted_data = dict(sorted(top_kind_to_count.items(), key=lambda item: item[1]))
        
        # Use barh for horizontal bar chart
        plt.barh(list(sorted_data.keys()), list(sorted_data.values()))
        plt.xlabel("Number of suppressions") 
        plt.ylabel("Kind of suppression") 
        plt.tight_layout()
        plt.savefig(output_file)
        print(f"Saved histogram to {output_file}")

    def _count_suppressions_by_category(self, suppressions):
        kinds = []
        for s in suppressions:
            kinds.extend(s.get_short_names())

        warning_to_numeric_code = get_warning_kind_to_numeric_code()
        category_to_count = Counter()
        for kind in kinds:
            if kind not in warning_to_numeric_code:
                print(f"Unknown kind: {kind}")
            else:
                code = warning_to_numeric_code[kind]
                category = code[0]
                category_to_count[category] += 1

        print(f"Category to count: {category_to_count}")

    def run(self):
        # prepare repositories
        self.get_repo_dirs()
        repo_dir_to_commit = self.checkout_latest_commits()

        # get suppressions
        all_suppressions = []
        for repo_dir, commit in repo_dir_to_commit.items():
            suppressions_file = super()._count_suppressions(repo_dir, commit)
            suppressions = read_suppressions_from_file(suppressions_file)
            all_suppressions.extend(suppressions)

        # compute and plot distribution
        self._plot_distribution(all_suppressions)

        # count suppressions by category
        self._count_suppressions_by_category(all_suppressions)


if __name__ == "__main__":
    exp = DistributionOfSuppressionOnLatestCommit()
    exp.repo_file = join("data", "python_repos_46_using_pylint.txt")
    exp.run()
