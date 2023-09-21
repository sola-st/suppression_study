import os
from os.path import join
from os import sep
import shutil
import subprocess
import tempfile

from suppression_study.utils.FunctionsCommon import get_commit_list
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


def get_commits_first_use_suppression(repo_dir, all_commit_id_list_startsfrom_oldest, all_commit_num):
    first_suppression_commit_index = 0
    if repo_dir.endswith(sep):
        repo_dir = repo_dir.rstrip(sep)
    repo_name = repo_dir_to_name(repo_dir)
    repo_parent_folder = os.path.dirname(repo_dir)

    with tempfile.TemporaryDirectory() as tmp_dir:
        grep_suppression_folder = join(tmp_dir, "grep")
        # Get the first commit that start using suppressions.
        for commit, commit_index in zip(all_commit_id_list_startsfrom_oldest, range(all_commit_num)):
            subprocess.run(
                ["python", "-m",  "suppression_study.suppression.GrepSuppressionPython",
                "--repo_dir=" + repo_dir,
                "--commit_id=" + commit,
                "--results_dir=" + tmp_dir]
            )

            suppression_csv_file_name = f"{commit}_suppression.csv"
            suppression_csv_file = join(grep_suppression_folder, suppression_csv_file_name)
            if os.path.exists(suppression_csv_file) and os.path.getsize(suppression_csv_file):
                first_suppression_commit_index = commit_index
                with open(f"{repo_parent_folder}_first_suppression_all_repos.csv", "a") as f:
                    f.write(f"{repo_name}, {commit}, {all_commit_num}, {commit_index}\n")
                break
            else: 
                # suppression exists in grep results, but not real suppressions, 
                # eg,. a suppression in a comment line
                shutil.rmtree(grep_suppression_folder)

    return first_suppression_commit_index


def select_1000_commits(repo_dir, all_commit_id_csv, selected_1000_commits_csv):
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

    all_commit_id_list = get_commit_list(all_commit_id_csv)
    all_commit_num = len(all_commit_id_list)

    # Find first_suppression_commit
    all_commit_id_list_startsfrom_oldest = list(reversed(all_commit_id_list))
    first_suppression_commit_index = get_commits_first_use_suppression(
            repo_dir, all_commit_id_list_startsfrom_oldest, all_commit_num)

    # Get the selected 1000 commits index range (final results includes commits and dates)
    with open(all_commit_id_csv, 'r') as f:
        commits_and_dates = f.readlines()
    commits_and_dates_startsfrom_oldest = list(reversed(commits_and_dates))

    expected_end_commit_index = first_suppression_commit_index + expected_select_commits_num
    if expected_end_commit_index > all_commit_num:
        # Get all the commits starts after first_suppression_commit (will be under 1000)
        expected_end_commit_index = all_commit_num - 1
    
    selected_1000_commits_dates = list(reversed(commits_and_dates_startsfrom_oldest[
            first_suppression_commit_index:expected_end_commit_index]))

    selected_1000_commits_dates_str = "".join(selected_1000_commits_dates)

    with open(selected_1000_commits_csv, "w") as f:
        f.writelines(selected_1000_commits_dates_str)