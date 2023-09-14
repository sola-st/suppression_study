import tempfile
import subprocess
import os
from os.path import join

from suppression_study.utils.FunctionsCommon import write_commit_info_to_csv


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
        
        actual_outputs = os.listdir(grep_folder)
        for a in actual_outputs:
            if a.endswith(".csv"):
                actual = join(demo_path, "grep", a)
                with open(actual, "r") as f:
                    actual_suppression = f.readlines()
                actual_suppression.sort()

                expected = join(grep_folder, a)
                with open(expected, "r") as f:
                    expected_suppression = f.readlines()
                expected_suppression.sort()

                for actual_sup, expected_sup in zip(actual_suppression, expected_suppression):
                    assert actual_sup == expected_sup

def test_GrepSuppressionPython_pylint_single_commit():
    expected_results = "tests/suppression/GrepSuppressionPython/PylintSuppression/a09fcfec_suppression.csv"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
            "--repo_dir=" + repo_dir,
            "--commit_id=a09fcfec",
            "--results_dir=" + demo_path])

        with open(expected_results, "r") as f:
            expected_suppression = f.readlines()
        expected_suppression.sort()

        with open(join(demo_path,"grep/a09fcfec_suppression.csv"), "r") as f:
            actual_suppression = f.readlines()
        actual_suppression.sort()
        
        assert len(actual_suppression) == len(expected_suppression)
        for actual_sup, expected_sup in zip(actual_suppression, expected_suppression):
            assert actual_sup == expected_sup

