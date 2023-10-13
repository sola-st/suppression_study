import csv
import time
import datetime
import json

class LifetimeCalculator():
    def __init__(self, all_main_commits, all_dates, suppression_history_json_file, lifetime_output_csv):
        self.all_main_commits = all_main_commits
        self.all_dates = all_dates
        self.suppression_history_json_file = suppression_history_json_file
        self.lifetime_output_csv = lifetime_output_csv

        self.lifetime_days = []
        self.lifetime_commit_rates = []
        self.lasting_mark_set = []

    def get_lifetime(self):
        total_commits_num = len(self.all_main_commits)
        default_start_date = self.all_dates[-1].strip().replace("\"", "")
        default_end_date = self.all_dates[0].strip().replace("\"", "")
        entire_lifetime = self.time_delta(default_start_date, default_end_date)

        print(f"Total commits num: {total_commits_num}")
        print(f"Entire lifetime: {entire_lifetime} days")

        self.calculate_lifetime_from_history(default_end_date, total_commits_num)
        self.write_lifetime()

        return entire_lifetime, total_commits_num

    def calculate_lifetime_from_history(self, default_end_date, total_commits_num):
        # Read the suppression histories, get the start/end date/commit to calculate lifetimes
        with open(self.suppression_history_json_file, 'r') as jf:
            json_strs = json.load(jf)

        right_range = len(json_strs)
        print(f"All Suppressions: {right_range}\n")

        for i in range(0, right_range):
            key = f"# S{i}"
            events = json_strs[i][key]
            events_num = len(events)
            end_commit = ""
            lasting_mark = 0  # 0->removed, 1->lasting, never removed

            start_date = json_strs[i][key][0]['date']
            start_commit = json_strs[i][key][0]['commit_id'][:8]
            expect_operation = json_strs[i][key][events_num - 1]['change_operation']

            if events_num > 1 and "delete" in expect_operation:  # change events(max 2), end of lifetime
                end_date = json_strs[i][key][1]['date']
                end_commit = json_strs[i][key][1]['commit_id'][:8]
                end_commit_index = self.all_main_commits.index(end_commit)
            else:
                end_date = default_end_date
                end_commit_index = total_commits_num - 1
                lasting_mark = 1
            self.lasting_mark_set.append(lasting_mark)

            # days
            start_date = start_date.replace("\"", "").strip()
            end_date = end_date.replace("\"", "").strip()
            day_delta = self.time_delta(start_date, end_date)
            self.lifetime_days.append(day_delta)

            # commit based rates
            start_commit_index = self.all_main_commits.index(start_commit)
            commit_delta = abs(end_commit_index - start_commit_index)
            rate = format(float(commit_delta / total_commits_num * 100), '.2f')
            self.lifetime_commit_rates.append(f"{rate}%")
        
    def time_delta(self, start_date, end_date):
        d1 = time.mktime(time.strptime(start_date, "%a %b %d %H:%M:%S %Y %z"))
        d2 = time.mktime(time.strptime(end_date, "%a %b %d %H:%M:%S %Y %z"))
        start = datetime.datetime.fromtimestamp(d1)
        end = datetime.datetime.fromtimestamp(d2)
        delta = abs((end - start).days)
        return delta
    
    def write_lifetime(self):
        # write calculated lifetime to a csv file
        length = len(self.lifetime_days)
        with open(self.lifetime_output_csv, 'a') as csvfile:
            csv_writer = csv.writer(csvfile)
            for index in range(0, length): # Suppression id, day, commit based rate, delete/never removed mark
                csv_writer.writerow([f"# S{index}", self.lifetime_days[index], self.lifetime_commit_rates[index], self.lasting_mark_set[index]])
   
