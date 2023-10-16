from typing import Dict, List
from os.path import join
import random
from json import dump
from git.repo import Repo
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name, get_name_of_main_branch
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
        repo_dir_to_histories = {}
        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            history_file = join("data", "results", repo_name,
                                "histories_suppression_level_all.json")
            histories = read_histories_from_json(history_file)
            repo_dir_to_histories[repo_dir] = histories
        return repo_dir_to_histories

    def _sample_commits(self, repo_dir_to_histories: Dict[str, List[List[ChangeEvent]]], filter: str):
        # logically, this should be a set, but let's keep it a list to make this experiment deterministic
        repo_dir_to_commit_urls = {}
        for repo_dir, histories in repo_dir_to_histories.items():
            repo_name = repo_dir_to_name(repo_dir)
            git_url_prefix = self.repo_name_to_git_url(repo_name)
            commit_urls = []
            for history in histories:
                for event in history:
                    if filter in event.change_operation:
                        url = git_url_prefix + "/commit/" + event.commit_id
                        if url not in commit_urls:
                            commit_urls.append(url)
            repo_dir_to_commit_urls[repo_dir] = commit_urls
        return repo_dir_to_commit_urls

    def _prepare_inspection_file(self, repo_dir_to_commit_urls, name):
        all_commit_urls = []
        for _, commit_urls in repo_dir_to_commit_urls.items():
            all_commit_urls.extend(commit_urls)

        # fixed seed to make the experiment deterministic
        my_random = random.Random(42)
        my_random.shuffle(all_commit_urls)

        inspection_dict = [{"url:": u, "comment": ""} for u in all_commit_urls]

        target_file = join("data", "results",
                           f"inspection_{name}_commits.json")
        with open(target_file, "w") as f:
            dump(inspection_dict, f, indent=4)

    def _commit_matches_keywords(self, commit, keywords):
        message = commit.message.lower()
        return any(k in message for k in keywords)

    def _filter_commits_by_keywords(self, repo_dir_to_commit_urls, keywords):
        nb_merge_commits = 0
        nb_non_merge_commits = 0
        repo_dir_to_filtered_commit_urls = {}
        for repo_dir, commit_urls in repo_dir_to_commit_urls.items():
            filtered_commit_urls = []
            repo = Repo(repo_dir)
            for commit_url in commit_urls:
                commit_id = commit_url.split("/")[-1]
                commit = repo.commit(commit_id)
                if self._commit_matches_keywords(commit, keywords):
                    filtered_commit_urls.append(commit_url)
                    print(
                        f"HIT ({'merge' if len(commit.parents) > 1 else 'non-merge'}), {commit_url}: {commit.message}")

                if len(commit.parents) > 1:
                    nb_merge_commits += 1
                else:
                    nb_non_merge_commits += 1
            repo_dir_to_filtered_commit_urls[repo_dir] = filtered_commit_urls

        print(f"Merge commits     : {nb_merge_commits}")
        print(f"Non-merge commits : {nb_non_merge_commits}")

        return repo_dir_to_filtered_commit_urls

    def _count_commits(self, repo_dir_to_commit_urls):
        ctr = 0
        for _, commit_urls in repo_dir_to_commit_urls.items():
            ctr += len(commit_urls)
        return ctr

    def _find_commits_based_on_histories(self, keywords):
        repo_dir_to_histories = self._read_suppression_histories()

        repo_dir_to_adding_commit_urls = self._sample_commits(
            repo_dir_to_histories, "add")
        repo_dir_to_removing_commit_urls = self._sample_commits(
            repo_dir_to_histories, "delete")

        # all commits that add or remove a suppression
        self._prepare_inspection_file(repo_dir_to_adding_commit_urls, "adding")
        self._prepare_inspection_file(
            repo_dir_to_removing_commit_urls, "deleting")

        # filter commits by keywords
        repo_dir_to_filtered_adding_commit_urls = self._filter_commits_by_keywords(
            repo_dir_to_adding_commit_urls, keywords)
        repo_dir_to_filtered_removing_commit_urls = self._filter_commits_by_keywords(
            repo_dir_to_removing_commit_urls, keywords)
        self._prepare_inspection_file(
            repo_dir_to_filtered_adding_commit_urls, "adding_filtered")
        self._prepare_inspection_file(
            repo_dir_to_filtered_removing_commit_urls, "deleting_filtered")

        print(
            f"Suppression-adding commits: {self._count_commits(repo_dir_to_adding_commit_urls)}")
        print(
            f"   ... with keywords      : {self._count_commits(repo_dir_to_filtered_adding_commit_urls)}")
        print(
            f"Suppression-removing commits: {self._count_commits(repo_dir_to_removing_commit_urls)}")
        print(
            f"   ... with keywords      : {self._count_commits(repo_dir_to_filtered_removing_commit_urls)}")

    def _find_in_all_commits(self, keywords):
        repo_dirs = self.get_repo_dirs()
        for repo_dir in repo_dirs:
            repo = Repo(repo_dir)
            branch = get_name_of_main_branch(repo)
            for commit in repo.iter_commits(branch):
                if self._commit_matches_keywords(commit, keywords):
                    print(f"HIT: {commit.message}")

    def run(self):
        self.checkout_latest_commits()

        # keywords = ["lint", "suppress", "warn",
        #             "clean", "fix", "remov", "disabl"]
        # keywords = ["lint", "suppress", "warn", "disabl"]
        keywords = ["lint"]

        self._find_commits_based_on_histories(keywords)
        self._find_in_all_commits(keywords)


if __name__ == '__main__':
    InspectSuppressionRelatedCommits().run()
