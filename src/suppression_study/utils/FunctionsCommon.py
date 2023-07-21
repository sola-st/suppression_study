class FunctionsCommon():
    
    def get_commit_list(commit_id_csv):
        all_commits = []
        with open(commit_id_csv, "r") as f: # 2 columns: commit and date
            line = f.readline()
            while line:
                commit = line.split(",")[0].replace("\"", "").strip()
                all_commits.append(commit)
                line = f.readline()
        return all_commits