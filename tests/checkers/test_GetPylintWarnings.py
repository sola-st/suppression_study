import subprocess

def test_waning_list():
    subprocess.run(["python3", "src/checkers/GetPylintWarnings.py",
        "--language=python", 
        "--repo_dir=/home/huimin/suppression_study/data/python/repositories/suppression-test-python-pylint/",
        "--commit_id=a09fcfe",
        "--grep_suppression_commit_level=/home/huimin/suppression_study/data/python/results/repositories/suppression-test-python-pylint/grep/a09fcfe.csv",
        "--results_dir=/home/huimin/suppression_study/data/python/results/repositories/suppression-test-python-pylint/test_results/"])

    with open("/home/huimin/suppression_study/data/python/results/repositories/suppression-test-python-pylint/test_results/commit_results/a09fcfe/a09fcfe_warnings.csv", "r") as f:
        warnings = f.readlines()
    f.close()
    
    assert warnings.__len__() == 4 # totally with 4 warnings
    for warn in warnings:
        meta = warn.split(",")
        assert meta.__len__() == 3 # meta: file_path, warning_type, line_number
        assert meta[0] == "folder1/bar.py"
