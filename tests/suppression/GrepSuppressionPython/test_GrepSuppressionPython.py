import tempfile
import subprocess
import os
from os.path import join

from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv
from tests.TestUtils import sort_and_compare_files


def test_GrepSuppressionPython_mypy_commit_list():
    grep_folder = "tests/suppression/GrepSuppressionPython/MypySuppression"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-mypy"
        demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-mypy.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)
        repo_dir = join(demo_path, demo_repo_name)

        commit_csv_file = join(repo_dir, "check_commits.csv")
        write_commit_info_to_csv(repo_dir, commit_csv_file)

        subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
            "--repo_dir=" + repo_dir ,
            "--commit_id=" + commit_csv_file,
            "--results_dir=" + demo_path])
        
        expected_csvs = os.listdir(grep_folder)
        for a in expected_csvs:
            if a.endswith(".csv"):
                actual_results = join(demo_path, "grep", a.replace("expected_", ""))
                expected_results = join(grep_folder, a)
                sort_and_compare_files(actual_results, expected_results)

def test_GrepSuppressionPython_pylint_single_commit():
    expected_results = "tests/suppression/GrepSuppressionPython/PylintSuppression/expected_a09fcfec_suppression.csv"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
            "--repo_dir=" + repo_dir,
            "--commit_id=a09fcfec",
            "--results_dir=" + demo_path])

        actual_results = join(demo_path,"grep/a09fcfec_suppression.csv")
        sort_and_compare_files(actual_results, expected_results)

