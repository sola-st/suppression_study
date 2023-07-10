import subprocess

def test_get_1000_commits():
    subprocess.run(["python3", "src/preprocess/Get1000Commits.py",
        "--all_commit_csv=/home/huimin/suppression_study/data/python/repositories/langflow/check_commits.csv"])

    with open("/home/huimin/suppression_study/data/python/repositories/langflow/check_commits_1000.csv", "r") as f:
        lines = f.readlines()
        assert lines.__len__() == 1000 
        commit_1st = lines[0].split(",")[0].replace("\"", "")
        commit_1000th = lines[-1].split(",")[0].replace("\"", "")
        assert commit_1st == "5807c92f" # Changes with latest commit
        assert commit_1000th == "4ba881d0" # 4ba881d0 should be real latest commit, otherwise both commit_1st and commit_1000th will "AssertionError"
        
if __name__=="__main__":
    test_get_1000_commits()