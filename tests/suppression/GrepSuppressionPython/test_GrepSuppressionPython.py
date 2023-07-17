import subprocess
import os
import shutil

def test_GrepSuppressionPython_mypy():
    initial_work_dir = os.getcwd()
    demo_path = "tests/suppression/GrepSuppressionPython/MypySuppression/"
    os.chdir(demo_path)
    demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-mypy.git"
    subprocess.run("git clone " + demo_repo_git_link, shell=True)
    os.chdir(initial_work_dir)

    subprocess.run(["python3", "src/suppression/GrepSuppressionPython.py",
        "--repo_dir=" + initial_work_dir + "/" + demo_path + "suppression-test-python-mypy/",
        "--commit_id=84a82b0",
        "--results_dir=" + initial_work_dir + "/" + demo_path])

    with open(demo_path + "84a82b0_suppression.csv", "r") as f:
        expected_suppression = f.readlines()

    with open(demo_path + "grep/84a82b0_suppression.csv", "r") as f:
        actual_suppression = f.readlines()
    
    assert len(actual_suppression) == len(expected_suppression)
    for actual_sup, expected_sup in zip(actual_suppression, expected_suppression):
        assert actual_sup == expected_sup

    shutil.rmtree(demo_path + "suppression-test-python-mypy/")  
    shutil.rmtree(demo_path + "grep/")

def test_GrepSuppressionPython_pylint():
    initial_work_dir = os.getcwd()
    demo_path = "tests/suppression/GrepSuppressionPython/PylintSuppression/"
    os.chdir(demo_path)
    demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
    subprocess.run("git clone " + demo_repo_git_link, shell=True)
    os.chdir(initial_work_dir)

    subprocess.run(["python3", "src/suppression/GrepSuppressionPython.py",
        "--repo_dir=" + initial_work_dir + "/" + demo_path + "suppression-test-python-pylint/",
        "--commit_id=a09fcfe",
        "--results_dir=" + initial_work_dir + "/" + demo_path])

    with open(demo_path + "a09fcfe_suppression.csv", "r") as f:
        expected_suppression = f.readlines()

    with open(demo_path + "grep/a09fcfe_suppression.csv", "r") as f:
        actual_suppression = f.readlines()
    
    assert len(actual_suppression) == len(expected_suppression)
    for actual_sup, expected_sup in zip(actual_suppression, expected_suppression):
        assert actual_sup == expected_sup

    shutil.rmtree(demo_path + "suppression-test-python-pylint/")  
    shutil.rmtree(demo_path + "grep/")

    