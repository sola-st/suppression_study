import os
import tempfile
import subprocess
from os.path import join

from suppression_study.utils.FunctionsCommon import FunctionsCommon


def test_LifetimeVisualization_toy_repo():
    expected_results = "tests/evolution/lifetime_visualization/lifetime_all_groups.csv"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-mypy"
        demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-mypy.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        commit_csv_file = join(repo_dir, "check_commits.csv")
        FunctionsCommon.write_commit_info_to_csv(repo_dir, commit_csv_file)
        
        output = "tests/evolution/lifetime_visualization/results/lifetime_all.csv"
        subprocess.run(["python", "-m", "suppression_study.evolution.lifetime_visualization.LifetimeVisualization",
            "--all_repositories_csv=tests/evolution/lifetime_visualization/all_repositories.csv", 
            f"--repo_parent_folder={demo_path}", 
            f"--lifetime_output_csv={output}"])

        with open(expected_results, "r") as f:
            expected_groups = f.readlines()

        with open("tests/evolution/lifetime_visualization/results/lifetime_all_groups.csv", "r") as f:
            actual_groups = f.readlines()
        
        assert len(expected_groups) == len(actual_groups)
        for actual, expected in zip(actual_groups, expected_groups):
            assert actual == expected

        restore()

def restore(): 
    # Based on the design of LifetimeVisualization, here do additional deletions besides tempfile
    filepath = "tests/evolution/lifetime_visualization/results"
    del_list = os.listdir(filepath)
    for f in del_list:
        file_path = os.path.join(filepath, f)
        if os.path.isfile(file_path):
            os.remove(file_path)