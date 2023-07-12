import subprocess
import os

def test_GetPylintWarning():
    initial_work_dir = os.getcwd()
    demo_path = "tests/checkers/demo/" # path
    os.chdir(demo_path)
    demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
    subprocess.run("git clone " + demo_repo_git_link, shell=True)
    os.chdir(initial_work_dir)

    subprocess.run(["python3", "src/checkers/GetPylintWarnings.py",
        "--repo_dir=" + demo_path + "suppression-test-python-pylint/",
        "--commit_id=a09fcfe",
        "--results_dir=../"])

    with open("tests/checkers/demo/expected_check_results/a09fcfe/a09fcfe_warnings.csv", "r") as f:
        expected_warnings = f.readlines()
    f.close()

    with open(demo_path + "checker_results/a09fcfe/a09fcfe_warnings.csv", "r") as f:
        actual_warnings = f.readlines()
    f.close()
    
    assert actual_warnings.__len__() == expected_warnings.__len__()
    for actual_warn, expected_warn in zip(actual_warnings, expected_warnings):
        assert actual_warn == expected_warn
        