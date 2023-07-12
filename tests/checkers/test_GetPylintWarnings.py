import subprocess
import os

def test_GetPylintWarning():
    demo_path = "demo/" # path
    if not os.path.exists(demo_path):
        os.makedirs(demo_path)
    os.chdir(demo_path)
    demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
    subprocess.run("git clone " + demo_repo_git_link, shell=True)
    os.chdir("../")

    subprocess.run(["python3", "src/checkers/GetPylintWarnings.py",
        "--repo_dir=" + demo_path + "suppression-test-python-pylint/",
        "--commit_id=a09fcfe",
        "--results_dir=../"])

    with open(demo_path + "checker_results/a09fcfe/a09fcfe_warnings.csv", "r") as f:
        warnings = f.readlines()
    f.close()
    
    assert warnings.__len__() == 2 # totally with 4 warnings in commit a09fcfe
    for warn in warnings:
        meta = warn.split(",")
        assert meta.__len__() == 3 # meta: file_path, warning_type, line_number
        assert meta[0] == "folder1/foo.py"
