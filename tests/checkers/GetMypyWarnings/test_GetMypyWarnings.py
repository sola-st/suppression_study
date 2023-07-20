import tempfile
import subprocess
from os.path import join

def test_GetMypyWarning():
    expected_results = "tests/checkers/GetMypyWarnings/06d4370_warnings.csv"
    with tempfile.TemporaryDirectory() as demo_path:
        demo_repo_name = "suppression-test-python-mypy"
        demo_repo_git_link = "https://github.com/Hhyemin/suppression-test-python-mypy.git"
        subprocess.run("git clone " + demo_repo_git_link, cwd=demo_path, shell=True)

        repo_dir = join(demo_path, demo_repo_name)
        subprocess.run(["python", "-m", "suppression_study.checkers.GetMypyWarnings",
            "--repo_dir=" + repo_dir,
            "--commit_id=06d4370",
            "--results_dir=" + demo_path])

        with open(expected_results, "r") as f:
            expected_warnings = f.readlines()

        with open(join(demo_path, "checker_results/06d4370/06d4370_warnings.csv"), "r") as f:
            actual_warnings = f.readlines()
        
        assert len(actual_warnings) == len(expected_warnings)
        for actual_warn, expected_warn in zip(actual_warnings, expected_warnings):
            assert actual_warn == expected_warn
