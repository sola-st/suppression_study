import argparse
import csv
import os
from os.path import join
from suppression_study.suppression.occurrences.GetOccurrencesPlot import visualization_occurrence

from suppression_study.suppression.occurrences.GetWarningTypesOccurrences import (
    get_warning_type_single_repository,
    write_warning_types_occurrences,
)

'''
Expected structure of results_repos_parent_folder:
results_repos_parent_folder (eg,. results/repositories)
    repo a (results/repositories/a)
        grep (results/repositories/a/grep)
        (other folder, eg,. the folder stores extracted history)
    repo b
    (other repos)
'''
parser = argparse.ArgumentParser(description="Get all the warning type and their occurrences, and visualize the results")
parser.add_argument("--all_repositories_csv", help=".csv file which stores information of a list of repositories", required=True)
parser.add_argument("--results_repos_parent_folder", 
        help="It contains subfolders named after different repositories to store corresponding results.", 
        required=True,)
parser.add_argument("--results_dir", help="Directory where to put the result csv file", required=True)
parser.add_argument("--type_source", 
        help="a mark that shows where the warning types come from, can be 'suppressions' or 'warnings'", 
        required=True)


def main(all_repositories_csv, results_repos_parent_folder, results_dir, type_source):
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
        # future work: instead of from grep folder, get suppressions from history json file.
        grep_folder = join(results_repos_parent_folder, repo_name, "grep")
        warning_type_occurrences_repo_csv = warning_type_occurrences_csv.replace(".csv", f"_{repo_name}.csv")
        raw_warning_types_repo_level = get_warning_type_single_repository(
            grep_folder, warning_type_occurrences_repo_csv
        )
        raw_warning_types_all.extend(raw_warning_types_repo_level)

    # Write all repositories' warning types and occurrences
    write_warning_types_occurrences(warning_type_occurrences_csv, raw_warning_types_all)
    visualization_occurrence(warning_type_occurrences_csv, type_source)


if __name__=="__main__":
    args = parser.parse_args()
    main(args.all_repositories_csv, args.results_repos_parent_folder, args.results_dir, args.type_source)