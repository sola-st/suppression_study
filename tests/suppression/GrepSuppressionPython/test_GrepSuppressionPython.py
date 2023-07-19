import subprocess
import os
import shutil


def test_GrepSuppressionPython_mypy_commit_list():
    initial_work_dir = os.getcwd()
    demo_path = "tests/suppression/GrepSuppressionPython/MypySuppression/"
    demo_repo_name = "suppression-test-python-mypy"
    os.chdir(demo_path)
    demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-mypy.git"
    subprocess.run("git clone " + demo_repo_git_link, shell=True)
    os.chdir(demo_repo_name)
    commit_command = "git log --reverse --pretty=format:'\"%h\",\"%cd\"'"
    git_get_commits = subprocess.run(commit_command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    commits = git_get_commits.stdout 

    with open(os.path.join("./check_commits_1000.csv"), "w") as f:
        f.writelines(commits)
    
    os.chdir(initial_work_dir)

    repo_dir = os.path.join(initial_work_dir, demo_path, demo_repo_name)
    subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
        "--repo_dir=" + repo_dir + "/",
        "--commit_id=" + repo_dir + "/check_commits_1000.csv",
        "--results_dir=" + initial_work_dir + "/" + demo_path])
    
    actual_outputs = os.listdir(demo_path + "grep/")
    for a in actual_outputs:
        if a.endswith(".csv"):
            actual = os.path.join(demo_path, "grep", a)
            with open(actual, "r") as f:
                actual_suppression = f.readlines()

            expected = actual.replace("/grep", "")
            with open(expected, "r") as f:
                expected_suppression = f.readlines()

            print(f"Comparing {actual} and {expected}")
            for actual_sup, expected_sup in zip(actual_suppression, expected_suppression):
                assert actual_sup == expected_sup

    shutil.rmtree(demo_path + demo_repo_name + "/")  
    shutil.rmtree(demo_path + "grep/")

def test_GrepSuppressionPython_pylint_single_commit():
    initial_work_dir = os.getcwd()
    demo_path = "tests/suppression/GrepSuppressionPython/PylintSuppression/"
    demo_repo_name = "suppression-test-python-pylint"
    os.chdir(demo_path)
    demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
    subprocess.run("git clone " + demo_repo_git_link, shell=True)
    os.chdir(initial_work_dir)

    repo_dir = os.path.join(initial_work_dir, demo_path, demo_repo_name)
    subprocess.run(["python", "-m", "suppression_study.suppression.GrepSuppressionPython",
        "--repo_dir=" + repo_dir + "/",
        "--commit_id=a09fcfe",
        "--results_dir=" + initial_work_dir + "/" + demo_path])

    with open(demo_path + "a09fcfe_suppression.csv", "r") as f:
        expected_suppression = f.readlines()

    with open(demo_path + "grep/a09fcfe_suppression.csv", "r") as f:
        actual_suppression = f.readlines()
    
    assert len(actual_suppression) == len(expected_suppression)
    for actual_sup, expected_sup in zip(actual_suppression, expected_suppression):
        assert actual_sup == expected_sup

    shutil.rmtree(demo_path + demo_repo_name + "/")  
    shutil.rmtree(demo_path + "grep/")
