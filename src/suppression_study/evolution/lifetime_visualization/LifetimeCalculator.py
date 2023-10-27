import csv
import time
import datetime
from suppression_study.evolution.ExtractHistory import read_histories_from_json

class LifetimeCalculator():
    def __init__(self, all_main_commits, all_dates, suppression_history_json_file, lifetime_output_csv):
        self.all_main_commits = all_main_commits
        self.all_dates = all_dates
        self.suppression_histories = read_histories_from_json(suppression_history_json_file)
        self.lifetime_output_csv = lifetime_output_csv

        self._filter_histories_by_date()

        self.lifetime_days = []
        self.lifetime_commit_rates = []
        self.lasting_mark_set = []

    def _filter_histories_by_date(self):
        '''
        Cover special cases: Some histories have their "add" event before the first commit in the selected 1000 commits.
        Problem: commit id out of range
        Reason: an initial third party suppression becomes a normal suppression later.

        For example,
            A suppression (xxx/lib/example.py # pylint: disable=protected-access) is recognized in a third party library in 10th commit. 
                (The extracted suppression history does not consider the suppressions from a third party library.)

            at a later point, in 20th commit, the suppression moved to another folder (xxx/music/example.py), is recognized as a normal suppression
                (The history extraction algorithm starts from 20th commit, as the 20th is regarded as the first commit introduces suppressions.)

            When use git log to go through all the histories, the result return the real start point is 10th commit.
            But the selected 1000 is [20, 1020], the 10 is out of this range.

        The filtered histories are correct (ground truth: source code).
        '''
        
        # The following code removes these histories.
        cleaned_histories = []
        for history in self.suppression_histories:
            ignore = False
            for change_event in history:
                if change_event.commit_id not in self.all_main_commits:
                    ignore = True
            if not ignore:
                cleaned_histories.append(history)
        self.suppression_histories = cleaned_histories

    def get_lifetime(self):
        total_commits_num = len(self.all_main_commits)
        default_start_date = self.all_dates[-1].strip().replace("\"", "")
        default_end_date = self.all_dates[0].strip().replace("\"", "")
        entire_lifetime = time_delta(default_start_date, default_end_date)

        print(f"Total commits num: {total_commits_num}")
        print(f"Entire lifetime: {entire_lifetime} days")

        nb_suppression_histories = self.calculate_lifetime_from_history(default_end_date, total_commits_num)
        self.write_lifetime()

        return entire_lifetime, total_commits_num, nb_suppression_histories

    def calculate_lifetime_from_history(self, default_end_date, total_commits_num):
        print(f"Number of suppression histories: {len(self.suppression_histories)}\n")

        for history in self.suppression_histories:
            end_commit = ""
            lasting_mark = 0  # 0->removed, 1->lasting, never removed
            start_date = history[0].date
            start_commit = history[0].commit_id[:8]
            expect_operation = history[-1].change_operation

            if len(history) > 1 and "delete" in expect_operation:  # change events(max 2), end of lifetime
                end_date = history[1].date
                end_commit = history[1].commit_id[:8]
                end_commit_index = self.all_main_commits.index(end_commit)
            else:
                end_date = default_end_date
                end_commit_index = total_commits_num - 1
                lasting_mark = 1
            self.lasting_mark_set.append(lasting_mark)

            # days
            start_date = start_date.replace("\"", "").strip()
            end_date = end_date.replace("\"", "").strip()
            day_delta = time_delta(start_date, end_date)
            self.lifetime_days.append(day_delta)

            # commit based rates
            start_commit_index = self.all_main_commits.index(start_commit)
            commit_delta = abs(end_commit_index - start_commit_index)
            rate = format(float(commit_delta / total_commits_num * 100), '.2f')
            self.lifetime_commit_rates.append(f"{rate}%")

        return len(self.suppression_histories)
    
    def write_lifetime(self):
        # write calculated lifetime to a csv file
        length = len(self.lifetime_days)
        with open(self.lifetime_output_csv, 'a') as csvfile:
            csv_writer = csv.writer(csvfile)
            for index in range(0, length): # Suppression id, day, commit based rate, delete/never removed mark
                csv_writer.writerow([f"# S{index}", self.lifetime_days[index], self.lifetime_commit_rates[index], self.lasting_mark_set[index]])
   
def time_delta(start_date, end_date):
    d1 = time.mktime(time.strptime(start_date, "%a %b %d %H:%M:%S %Y %z"))
    d2 = time.mktime(time.strptime(end_date, "%a %b %d %H:%M:%S %Y %z"))
    start = datetime.datetime.fromtimestamp(d1)
    end = datetime.datetime.fromtimestamp(d2)
    delta = abs((end - start).days)
    return delta