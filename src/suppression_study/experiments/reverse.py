import csv
from os.path import join
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.FunctionsCommon import get_commit_date_lists
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class Get1000Commits(Experiment):
    def run(self):
        # prepare repositories
        repo_dirs = self.get_repo_dirs()
        self.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            commit_list_file = join("data", "results", repo_name, "commit_id_list.csv")
            commit_list, date_list = get_commit_date_lists(commit_list_file)
            commit_list.reverse()
            date_list.reverse()

            output = commit_list_file.replace(".csv", "_old_new.csv")
            with open(output, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                for commit, date in zip(commit_list, date_list):
                    csv_writer.writerow([commit, date])

if __name__ == "__main__":
    Get1000Commits().run()