import tempfile
import subprocess
import json
from os.path import join

from suppression_study.evolution.Select1000Commits import select_1000_commits


def test_ExtractHistory_pylint_single_branch():
    expected_results = "tests/evolution/expected_histories_suppression_level_all.json"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        selected_1000_commits_csv = join(repo_dir, "check_commits_1000.csv")
        select_1000_commits(repo_dir, selected_1000_commits_csv)
        subprocess.run(["python", "-m", "suppression_study.evolution.ExtractHistory",
            "--repo_dir=" + repo_dir,
            "--selected_1000_commits_csv=" + selected_1000_commits_csv,
            "--results_dir=" + demo_path])

        with open(expected_results, "r") as f:
            expected_history = json.load(f)

        with open(join(demo_path,"histories_suppression_level_all.json"), "r") as f:
            actual_history = json.load(f)
        
        assert len(actual_history) == len(expected_history)
        assert actual_history == expected_history

def test_ExtractHistory_pylint_multi_branch():
    expected_results = "tests/evolution/expected_histories_multi_branch.json"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-multi-operation"
        demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-multi-operation.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        selected_1000_commits_csv = join(repo_dir, "check_commits_1000.csv")
        select_1000_commits(repo_dir, selected_1000_commits_csv)
        subprocess.run(["python", "-m", "suppression_study.evolution.ExtractHistory",
            "--repo_dir=" + repo_dir,
            "--selected_1000_commits_csv=" + selected_1000_commits_csv,
            "--results_dir=" + demo_path])

        with open(expected_results, "r") as f:
            expected_history = json.load(f)

        with open(join(demo_path,"histories_suppression_level_all.json"), "r") as f:
            actual_history = json.load(f)
        
        assert len(actual_history) == len(expected_history)
        assert actual_history == expected_history