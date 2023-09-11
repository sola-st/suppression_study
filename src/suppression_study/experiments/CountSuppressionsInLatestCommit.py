from suppression_study.experiments.Experiment import Experiment


class CountSuppressionsInLatestCommit(Experiment):
    def run(self):
        for repo_dir in self.get_repo_dirs():
            print(repo_dir)
        self.checkout_latest_commits()


if __name__ == "__main__":
    CountSuppressionsInLatestCommit().run()
