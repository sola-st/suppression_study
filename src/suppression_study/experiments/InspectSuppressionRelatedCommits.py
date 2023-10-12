from typing import Dict, List
from os.path import join
import random
from json import dump
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name
from suppression_study.evolution.ExtractHistory import read_histories_from_json
from suppression_study.evolution.ChangeEvent import ChangeEvent


class InspectSuppressionRelatedCommits(Experiment):
    """
    Randomly samples commits that either add or remove a suppression,
    and prepares them for manual inspection.

    Depends on:
     * ComputeSuppressionHistories
    """

    def _read_suppression_histories(self) -> Dict[str, List[List[ChangeEvent]]]:
        repo_dirs = self.get_repo_dirs()
        repo_name_to_histories = {}
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            history_file = join("data", "results", repo_name,
                                "histories_suppression_level_all.json")
            histories = read_histories_from_json(history_file)
            repo_name_to_histories[repo_name] = histories
        return repo_name_to_histories

    def _sample_commits(self, repo_name_to_histories: Dict[str, List[List[ChangeEvent]]], filter: str):
        # logically, this should be a set, but let's keep it a list to make this experiment deterministic
        commit_urls = []
        for repo_name, histories in repo_name_to_histories.items():
            git_url_prefix = self.repo_name_to_git_url(repo_name)
            for history in histories:
                for event in history:
                    if filter in event.change_operation:
                        url = git_url_prefix + "/commit/" + event.commit_id
                        if url not in commit_urls:
                            commit_urls.append(url)
        return commit_urls

    def _prepare_inspection_file(self, commit_urls, name):
        # fixed seed to make the experiment deterministic
        my_random = random.Random(42)
        my_random.shuffle(commit_urls)

        inspection_dict = [{"url:": u, "comment": ""} for u in commit_urls]

        target_file = join("data", "results", f"inspection_{name}_commits.json")
        with open(target_file, "w") as f:
            dump(inspection_dict, f, indent=4)

    def run(self):
        repo_name_to_histories = self._read_suppression_histories()

        adding_commit_urls = self._sample_commits(
            repo_name_to_histories, "add")
        removing_commit_urls = self._sample_commits(
            repo_name_to_histories, "delete")

        self._prepare_inspection_file(adding_commit_urls, "adding")
        self._prepare_inspection_file(removing_commit_urls, "deleting")


if __name__ == '__main__':
    InspectSuppressionRelatedCommits().run()
