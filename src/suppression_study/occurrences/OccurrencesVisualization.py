import argparse
import csv
import os
from os.path import join
from suppression_study.occurrences.GetOccurrencesPlot import visualization_occurrence

from suppression_study.occurrences.GetWarningTypesOccurrences import (
    get_warning_type_single_repository,
    write_warning_types_occurrences,
)

'''
Expected structure of grep_parent_folder:
grep_parent_folder (eg,. results/repositories)
    repo a (results/repositories/a)
        grep (results/repositories/a/grep)
        (other folder, eg,. the folder stores extracted history)
    repo b
    (other repos)
'''
parser = argparse.ArgumentParser(description="Get all the warning type and their occurrences, and visualize the results")
parser.add_argument("--all_repositories_csv", help=".csv file which stores information of a list of repositories", required=True)
parser.add_argument(
    "--grep_parent_folder",
    help=f"the folder where stores the results of all repositories, expected with subfolders for each repository."
        f"and the experimental results are in the subfolders.",
    required=True,
)
parser.add_argument("--results_dir", help="Directory where to put the result csv file", required=True)


def main(all_repositories_csv, grep_parent_folder, results_dir):
    # Get raw warning types from all specified repositories.
    occurrences_folder = join(results_dir, "occurrences")
    if not os.path.exists(occurrences_folder):
        os.makedirs(occurrences_folder)
    warning_type_occurrences_csv = join(occurrences_folder, "warning_types_occurrences.csv")

    raw_warning_types_all = []
    csv_reader = csv.reader(open(all_repositories_csv))
    for repo in csv_reader:
        repo_name = repo[1]
        print(f"Repository: {repo_name}")
        grep_folder = join(grep_parent_folder, repo_name, "grep")
        warning_type_occurrences_repo_csv = warning_type_occurrences_csv.replace(".csv", f"_{repo_name}.csv")
        raw_warning_types_repo_level = get_warning_type_single_repository(
            grep_folder, warning_type_occurrences_repo_csv
        )
        raw_warning_types_all.extend(raw_warning_types_repo_level)

    # Write all repositories' warning types and occurrences
    write_warning_types_occurrences(warning_type_occurrences_csv, raw_warning_types_all)
    visualization_occurrence(warning_type_occurrences_csv)


if __name__=="__main__":
    args = parser.parse_args()
    main(args.all_repositories_csv, args.grep_parent_folder, args.results_dir)