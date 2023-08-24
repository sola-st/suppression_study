from os.path import join
import tempfile
import subprocess


def test_mapping():
    with tempfile.TemporaryDirectory() as working_dir:
        repo_name = "suppression-test-suppr-warn-map"
        repo_url = "https://github.com/michaelpradel/suppression-test-suppr-warn-map.git"
        subprocess.run(f"git clone {repo_url}", cwd=working_dir, shell=True)
        
        repo_dir = join(working_dir, repo_name)

        subprocess.run(["python", "-m", "suppression_study.warnings.WarningSuppressionMapper",
            "--repo_dir=" + repo_dir,
            "--commit_id=7178e72",
            "--lang=python",
            "--checker=pylint",
            "--results_dir=" + working_dir])
        
        with open("tests/warnings/WarningSuppressionMapper/expected.csv", "r") as f:
            expected_lines = f.readlines()
        expected_lines.sort()

        with open(join(working_dir, "7178e72_mapping.csv"), "r") as f:
            actual_lines = f.readlines()
        actual_lines.sort()

        assert len(actual_lines) == len(expected_lines)
        for actual, expected in zip(actual_lines, expected_lines):
            assert actual == expected