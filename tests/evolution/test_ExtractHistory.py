import tempfile
import subprocess
from os.path import join


def test_ExtractHistory_pylint():
    expected_results = "tests/evolution/histories_suppression_level_all.json"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-pylint"
        demo_repo_git_link = "https://github.com/michaelpradel/suppression-test-python-pylint.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        commit_csv_file = join(repo_dir, "check_commits.csv")
        subprocess.run(["python", "-m", "suppression_study.evolution.ExtractHistory",
            "--repo_dir=" + repo_dir,
            "--commit_id=" + commit_csv_file,
            "--results_dir=" + demo_path])

        with open(expected_results, "r") as f:
            expected_history = f.readlines()
        expected_history.sort()

        with open(join(demo_path,"gitlog_history/histories_suppression_level_all.json"), "r") as f:
            actual_history= f.readlines()
        actual_history.sort()
        
        assert len(actual_history) == len(expected_history)
        for actual, expected in zip(actual_history, expected_history):
            assert actual == expected

if __name__=="__main__":
    test_ExtractHistory_pylint()