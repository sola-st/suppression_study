from os.path import join
from suppression_study.evolution.lifetime_visualization.GetLifetimeGroupsInfo import GetLifetimeGroupsInfo
from suppression_study.evolution.lifetime_visualization.GetLifetimePlot import visualize_lifetime
from suppression_study.evolution.lifetime_visualization.LifetimeCalculator import LifetimeCalculator
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.FunctionsCommon import get_commit_date_lists
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class VisualizeLifetimeForAllSuppressions(Experiment):
    """
    Experiment that run GrepSuppressionPython on all commits. 
    Get suppressions in given repositories, and get a csv file which 
    show the number of suppressions in every commit.
    """

    def run(self):
        entire_lifetime_set = []
        total_commits_num_set = []
        num_groups = 5 # The number of columns in the expected plot
        '''
        expected lifetime_output_csv contains: 
            suppression ID, 
            remaining days, 
            rates, = remaining commits num / main branch commits num
            remaining_mark (deleted, or never removed)
        '''
        lifetime_output_csv = join("data", "results", "lifetime.csv")
    
        # prepare repositories
        repo_dirs = self.get_repo_dirs()

        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            print(f"Repository: {repo_name}")
            all_main_commits_csv = join("data", "results", repo_name, "commit_id_list.csv") # only main branch
            all_commits, all_dates = get_commit_date_lists(all_main_commits_csv)
            suppression_history_json_file = join("data", "results", repo_name, "histories_suppression_level_all.json")
            # Start get lifetime
            # Write a file 'output_individual_repository', which records lifetime of all suppressions in current repository
            init = LifetimeCalculator(all_commits, all_dates, suppression_history_json_file, lifetime_output_csv)
            entire_lifetime, total_commits_num = init.get_lifetime()
            # Collect lifetime and commits_num for each repository
            entire_lifetime_set.append(int(entire_lifetime))
            total_commits_num_set.append(total_commits_num)

        # Decide the lifetime range and commit range for all the repositories
        max_entire_lifetime = 0
        for t in entire_lifetime_set:
            max_entire_lifetime = max(max_entire_lifetime, t)
        max_total_commits = 0
        for c in total_commits_num_set:
            max_total_commits = max(max_total_commits, c)
        print(f"For all repositories, max_entire_lifetime, max_total_commits: {max_entire_lifetime}, {max_total_commits}")

        # Get groups for extracting plot
        lifetime_groups_csv = lifetime_output_csv.replace(".csv", "_groups.csv") # For all repositories
        # Based on lifetime_output_csv, process and write to lifetime_groups_csv
        GetLifetimeGroupsInfo(max_entire_lifetime, max_total_commits, lifetime_output_csv, lifetime_groups_csv, num_groups).get_groups()
        visualize_lifetime(lifetime_groups_csv)


if __name__ == "__main__":
    VisualizeLifetimeForAllSuppressions().run()