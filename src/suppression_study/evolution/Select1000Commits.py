import csv
import os
from os.path import join, dirname, exists
import shutil
import subprocess
import tempfile

from suppression_study.utils.FunctionsCommon import get_commit_list, write_commit_info_to_csv
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


def get_commits_first_use_suppression(repo_dir, all_main_commit_id_list_startsfrom_oldest, all_main_commit_num, main_commits_suppression_folder):
    # Return the first commit that firstly introduces suppressions and its index
    with tempfile.TemporaryDirectory() as tmp_dir:
        grep_suppression_folder = join(tmp_dir, "grep")
        # Get the first commit that start using suppressions.
        for commit, commit_index in zip(all_main_commit_id_list_startsfrom_oldest, range(all_main_commit_num)):
            suppression_csv_file_name = f"{commit}_suppression.csv"
            if main_commits_suppression_folder:
                suppression_csv_file = join(main_commits_suppression_folder, suppression_csv_file_name)
            else:
                subprocess.run(
                    ["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
                    "--repo_dir=" + repo_dir,
                    "--commit_id=" + commit,
                    "--results_dir=" + tmp_dir,])
                suppression_csv_file = join(grep_suppression_folder, suppression_csv_file_name)
                
            if os.path.exists(suppression_csv_file) and os.path.getsize(suppression_csv_file):
                return commit, commit_index  # first_suppression_commit and its index
            elif os.path.exists(grep_suppression_folder):
                # suppression exists in grep results, but not real suppressions,
                # eg,. a suppression in a comment line
                shutil.rmtree(grep_suppression_folder)


def select_1000_commits(repo_dir, selected_1000_commits_csv, overall_information_csv=None):
    # overall_information_csv is designed to record the start and end of the selected 1000 commits.
    # especially when run this function on all repositories. [Actual usage example: experiment/Get1000Commits.py]
    '''
    Select 1000 commits for each repository:
    start from the commit that first introduces suppressions (Assume it called "first_suppression_commit")
    With 2 options:
    first_suppression_commit_index starts from 0,
    all_commits_num is absolute number.
    1) get the 1000 commits starts from first_suppression_commit
        start: first_suppression_commit | end: the following 1000 commits (includes start)
    2) get the "latest" 1000 commits include first_suppression_commit
        (may smaller than 1000 commits, as much as possible)
        start: the previous 1000 commits (includes end)  | end: the "latest" commit
    Results: write the selected 1000 commits to a csv file
    '''

    expected_select_commits_num = 1000
    selected_1000_commits_dates = []

    all_main_commit_id_csv = selected_1000_commits_csv.replace("_1000", "")
    if not os.path.exists(all_main_commit_id_csv):
        write_commit_info_to_csv(repo_dir, all_main_commit_id_csv)  # commit_info: commit and date

    all_commit_id_list = get_commit_list(all_main_commit_id_csv)
    all_main_commit_num = len(all_commit_id_list)

    # Find first_suppression_commit
    all_main_commit_id_list_startsfrom_oldest = list(reversed(all_commit_id_list))
    # check if the suppression are already extracted
    repo_name = repo_dir.rsplit("/", 1)[1].strip()
    main_commits_suppression_folder = join("data", "results", repo_name, "main_commits_suppression_pylint")
    if not exists(main_commits_suppression_folder):
        main_commits_suppression_folder = None
    first_suppression_commit, first_suppression_commit_index = get_commits_first_use_suppression(
        repo_dir, all_main_commit_id_list_startsfrom_oldest, all_main_commit_num, main_commits_suppression_folder
    )

    # Get the selected 1000 commits index range (final results includes commits and dates)
    with open(all_main_commit_id_csv, 'r') as f:
        commits_and_dates = f.readlines()
    commits_and_dates_startsfrom_oldest = list(reversed(commits_and_dates))

    expected_end_commit_index = first_suppression_commit_index + expected_select_commits_num
    real_end_commit_index_startsfrom_zero = expected_end_commit_index - 1
    if expected_end_commit_index > all_main_commit_num:
        # Get all the commits starts after first_suppression_commit (will be under 1000)
        real_end_commit_index_startsfrom_zero = all_main_commit_num - 1

    selected_1000_commits_dates = list(
        reversed(commits_and_dates_startsfrom_oldest[first_suppression_commit_index:expected_end_commit_index])
    )

    selected_1000_commits_dates_str = "".join(selected_1000_commits_dates)

    with open(selected_1000_commits_csv, "w") as f:
        f.writelines(selected_1000_commits_dates_str)

    # copy the extracted suppression for the selected 1000 to a "grep" folder.
    if main_commits_suppression_folder:
        grep_folder = join("data", "results", repo_name, "grep")
        os.makedirs(grep_folder, exist_ok=True)
        selected_1000_commit_id_list = all_main_commit_id_list_startsfrom_oldest[first_suppression_commit_index:expected_end_commit_index]
        for commit in selected_1000_commit_id_list:
            suppression_csv_file_name = f"{commit}_suppression.csv"
            source_suppression_csv_file = join(main_commits_suppression_folder, suppression_csv_file_name)
            target_suppression_csv_file = join(grep_folder, suppression_csv_file_name)
            shutil.copyfile(source_suppression_csv_file, target_suppression_csv_file)

    if overall_information_csv != None:
        # record the selected 1000's first and end commit information
        # repo_name, all_main_commit_num, first_commit, first_commit_index, end_commit, end_commit_index
        os.makedirs(dirname(overall_information_csv), exist_ok=True)
        repo_name = repo_dir_to_name(repo_dir)
        real_end_commit = all_main_commit_id_list_startsfrom_oldest[real_end_commit_index_startsfrom_zero]
        with open(overall_information_csv, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(
                [
                    repo_name,
                    all_main_commit_num,
                    first_suppression_commit,
                    first_suppression_commit_index,
                    real_end_commit,
                    real_end_commit_index_startsfrom_zero,
                ]
            )