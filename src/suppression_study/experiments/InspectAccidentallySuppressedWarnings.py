import json
from typing import Dict, List
from os.path import join
import random
from json import dump
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name
from suppression_study.evolution.ChangeEvent import ChangeEvent


class InspectSuppressionRelatedCommits(Experiment):
    """
    Randomly samples commits that regarded as having accidentally suppressed warnings.

    Depends on:
     * ComputeAccidentallySuppressedWarnings
    """

    def _read_accidentally_suppressed_warnings(self) -> Dict[str, List[List[ChangeEvent]]]:
        repo_dirs = self.get_repo_dirs()
        repo_name_to_acci_commits = {}
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            acci_warning_file = join("data", "results", repo_name,
                                "accidentally_suppressed_warnings.json")
            with open(acci_warning_file, "r") as f:
                records_data = json.load(f)
            repo_name_to_acci_commits[repo_name] = records_data
        return repo_name_to_acci_commits

    def _sample_commits(self, repo_name_to_acci_commits):
        url_and_data = []
        for repo_name, acci_data in repo_name_to_acci_commits.items():
            if acci_data:
                git_url_prefix = self.repo_name_to_git_url(repo_name)
                for acci in acci_data:
                    url = git_url_prefix + "/commit/" + acci["commit"]
                    if url not in url_and_data:
                        url_and_data.append([url, acci])
        return url_and_data

    def _prepare_inspection_file(self, url_and_data):
        # fixed seed to make the experiment deterministic
        my_random = random.Random(42)
        my_random.shuffle(url_and_data)

        inspection_dict = [{"Check": u, "comment": ""} for u in url_and_data]

        target_file = join("data", "results", f"inspection_accidental_commits.json")
        with open(target_file, "w") as f:
            dump(inspection_dict, f, indent=4)

    def run(self):
        repo_name_to_acci_commits = self._read_accidentally_suppressed_warnings()
        url_and_data = self._sample_commits(
            repo_name_to_acci_commits)

        self._prepare_inspection_file(url_and_data)


if __name__ == '__main__':
    InspectSuppressionRelatedCommits().run()
