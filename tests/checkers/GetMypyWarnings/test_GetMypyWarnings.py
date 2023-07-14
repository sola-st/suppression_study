import subprocess
import os
import shutil

def test_GetMypyWarning():
    initial_work_dir = os.getcwd()
    demo_path = "tests/checkers/GetMypyWarnings/"
    os.chdir(demo_path)
    demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-mypy.git"
    subprocess.run("git clone " + demo_repo_git_link, shell=True)
    os.chdir(initial_work_dir)

    subprocess.run(["python3", "src/checkers/GetMypyWarnings.py",
        "--repo_dir=" + demo_path + "suppression-test-python-mypy/",
        "--commit_id=06d4370",
        "--results_dir=../"])

    with open(demo_path + "/06d4370_warnings.csv", "r") as f:
        expected_warnings = f.readlines()

    with open(demo_path + "checker_results/06d4370/06d4370_warnings.csv", "r") as f:
        actual_warnings = f.readlines()
    
    assert len(actual_warnings) == len(expected_warnings)
    for actual_warn, expected_warn in zip(actual_warnings, expected_warnings):
        assert actual_warn == expected_warn


    shutil.rmtree(demo_path + "suppression-test-python-mypy/")  
    shutil.rmtree(demo_path + "checker_results/")
