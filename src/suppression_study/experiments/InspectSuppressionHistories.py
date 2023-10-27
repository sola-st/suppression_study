from typing import Dict, List
from os.path import join
import random
from json import dump
from suppression_study.evolution.ChangeEvent import ChangeEvent, get_change_event_dict
from suppression_study.evolution.ExtractHistory import read_histories_from_json
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class InspectSuppressionHistories(Experiment):
    """
    Shuffle all extracted suppression histories.
    Get the add and delete commit git urls for the corresponding change event.

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

    def _sample_commits(self, repo_name_to_histories: Dict[str, List[List[ChangeEvent]]]):
        url_and_histories = []
        for repo_name, histories in repo_name_to_histories.items():
            git_url_prefix = self.repo_name_to_git_url(repo_name)
            for history in histories:
                commit_urls = []
                history_dict = []
                for event in history:
                    url = git_url_prefix + "/commit/" + event.commit_id
                    event_dict = get_change_event_dict(event)
                    # commit_urls at most has 2 urls, 
                    # one for add events, and optionally has another one for delete event
                    commit_urls.append(url)
                    history_dict.append(event_dict)
                commit_urls.extend(history_dict)
                url_and_histories.append(commit_urls)
        return url_and_histories

    def _prepare_inspection_file(self, url_and_histories):
        my_random = random.Random(42)
        my_random.shuffle(url_and_histories)

        inspection_dict = [{"Check": u, "comment": ""} for u in url_and_histories]

        target_file = join("data", "results", f"inspection_suppression_histories.json")
        with open(target_file, "w") as f:
            dump(inspection_dict, f, indent=4)

    def run(self):
        repo_name_to_histories = self._read_suppression_histories()
        url_and_histories = self._sample_commits(repo_name_to_histories)
        self._prepare_inspection_file(url_and_histories)


if __name__ == '__main__':
    InspectSuppressionHistories().run()
