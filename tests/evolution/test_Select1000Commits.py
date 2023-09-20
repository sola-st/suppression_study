import tempfile
import subprocess
from os.path import join
from suppression_study.evolution.Select1000commits import select_1000_commits
from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv

from tests.TestUtils import sort_and_compare_files


def test_ExtractHistory_pylint():
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        commit_csv_file = join(repo_dir, "check_commits.csv")
        write_commit_info_to_csv(repo_dir, commit_csv_file)
        actual_result_file = join(repo_dir, "selected_1000_commits.csv")
        select_1000_commits(repo_dir, commit_csv_file, actual_result_file)
        
        expected_results_file = "tests/evolution/expected_selected_1000_commits.csv"
        sort_and_compare_files(actual_result_file, expected_results_file)