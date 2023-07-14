from tempfile import TemporaryDirectory
from suppression_study.util import RepoUtil
import json


class WarningHistoryCreator():
    def __init__(self, repo_dir, WarningExtractor):
        self.repo_dir = repo_dir
        self.WarningExtractor = WarningExtractor
        self.warning_id_to_history = {}

    def __compute_warnings(self, tmp_dir):
        all_commits = RepoUtil.all_commits(self.repo_dir)
        for commit in all_commits:
            commit_id = commit.hexsha[0:7]
            self.WarningExtractor.main(self.repo_dir, commit_id, tmp_dir)                

    def create_history(self):
        with TemporaryDirectory() as tmp_dir:
            self.__compute_warnings(tmp_dir)

    def to_json(self, dest_file):
        with open(dest_file, "w") as f:
            json.dump(self.warning_id_to_history, f)