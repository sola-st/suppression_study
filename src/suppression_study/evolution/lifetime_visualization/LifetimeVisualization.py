import argparse
import csv
import os

from suppression_study.evolution.lifetime_visualization.GetLifetimeGroupsInfo import GetLifetimeGroupsInfo
from suppression_study.evolution.lifetime_visualization.LifetimeCalculator import LifetimeCalculator
from suppression_study.evolution.lifetime_visualization.GetLifetimePlot import visualize_lifetime

from suppression_study.utils.FunctionsCommon import FunctionsCommon


parser = argparse.ArgumentParser(description="Calculate lifetime for all suppressions, and visualize the results") 
parser.add_argument("--all_repositories_csv", help=".csv file which stores information of a list of repositories", required=True)
parser.add_argument("--repo_parent_folder", help="the folder where stores the csv listed repositories", required=True)
parser.add_argument("--lifetime_output_csv", help=".csv file which to write the calculated lifetime results", required=True)


def main(all_repositories_csv, repo_parent_folder, lifetime_output_csv):
    '''
    Read file 'all_repositories_csv' to iteratively process all the repositories, finally get 2 files
    1) Write calculated lifetime results to customized file lifetime_output_csv 
    2) Write groups to which will be used for extracting a plot to show the results
    '''
    entire_lifetime_set = []
    total_commits_num_set = []
    num_groups = 5 # The number of columns in the expected plot
    results_folder = lifetime_output_csv.rsplit("/",1)[0]

    csv_reader = csv.reader(open(all_repositories_csv))
    for repo in csv_reader:
        repo_name = repo[1]
        print(f"Repository: {repo_name}")
        repo_dir = f"{repo_parent_folder}/{repo_name}"
        all_commits_csv_file = f"{repo_dir}/check_commits.csv"
        if not os.path.exists(all_commits_csv_file):
            FunctionsCommon.write_commit_info_to_csv(repo_dir, all_commits_csv_file)
        # Read all_commits_csv_file, get 2 lists: all_commit, all_dates
        all_commits, all_dates = FunctionsCommon.get_commit_date_lists(all_commits_csv_file)
        suppression_history_json_file = f"{results_folder}/{repo_name}/gitlog_history/histories_suppression_level_all.json"
        # Start get lifetime
        # Write a file 'output_individual_repository', which records lifetime of all suppressions in current repository
        init = LifetimeCalculator(all_commits, all_dates, suppression_history_json_file, lifetime_output_csv)
        entire_lifetime, total_commits_num = init.get_lifetime()
        # Collect lifetime and commits_num for each repository
        entire_lifetime_set.append(int(entire_lifetime))
        total_commits_num_set.append(total_commits_num)

    # Decide the lifetime range and commit range for all the repositories
    max_entire_lifetime = 0
    for t in entire_lifetime_set:
        max_entire_lifetime = max(max_entire_lifetime, t)
    max_total_commits = 0
    for c in total_commits_num_set:
        max_total_commits = max(max_total_commits, c)
    print(f"For all repositories, max_entire_lifetime, max_total_commits: {max_entire_lifetime}, {max_total_commits}")

    # Get groups for extracting plot
    lifetime_groups_csv = lifetime_output_csv.replace(".csv", "_groups.csv") # For all repositories
    # Based on lifetime_output_csv, process and write to lifetime_groups_csv
    GetLifetimeGroupsInfo(max_entire_lifetime, max_total_commits, lifetime_output_csv, lifetime_groups_csv, num_groups).get_groups()
    visualize_lifetime(lifetime_groups_csv)


if __name__=="__main__":
    args = parser.parse_args()
    main(args.all_repositories_csv, args.repo_parent_folder, args.lifetime_output_csv)