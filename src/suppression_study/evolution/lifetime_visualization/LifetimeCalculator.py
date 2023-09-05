import time
import datetime
import json
import re

class LifetimeCalculator():
    def __init__(self, all_commits, all_dates, suppression_history_json_file, lifetime_output_csv):
        self.all_commits = all_commits
        self.all_dates = all_dates
        self.suppression_history_json_file = suppression_history_json_file
        self.lifetime_output_csv = lifetime_output_csv

    def get_lifetime(self):
        total_commits_num = self.all_commits.__len__()
        default_start_date = self.all_dates[-1].strip().replace("\"", "")
        default_end_date = self.all_dates[0].strip().replace("\"", "")
        entire_lifetime = self.time_delta("", default_start_date, default_end_date)
        entire_lifetime = int(re.sub("\D", "", entire_lifetime))

        print(f"Total commits num: {total_commits_num}")
        print(f"Entire lifetime: {entire_lifetime} days")

        lifetime_days, lifetime_commits, lasting_mark_set = \
                self.calculate_lifetime_from_history(default_end_date, total_commits_num)

        to_write = ""
        length = lifetime_days.__len__()
        for index in range(0, length): # Suppression id, day, commit, commit based rate
            to_write = f"{to_write}{lifetime_days[index]},{lifetime_commits[index]},{lasting_mark_set[index]}\n"

        # Accelerate current results to all, write to a csv file
        with open(self.lifetime_output_csv, "a") as f: # For all repositories
            f.write(to_write)

        return entire_lifetime, total_commits_num

    def calculate_lifetime_from_history(self, default_end_date, total_commits_num):
        # Read the suppression histories, get the start/end date/commit to calculate lifetimes
        lifetime_days = []
        lifetime_commits = []
        lasting_mark_set = []

        with open(self.suppression_history_json_file, 'r') as jf:
            json_strs = json.load(jf)

        right_range = json_strs.__len__()
        print(f"All Suppressions: {right_range}\n")

        for index_1 in range(0, right_range):
            key = "# S" + str(index_1)
            events = json_strs[index_1][key]
            events_num = events.__len__()
            end_commit = ""
            lasting_mark = 0  # 0->removed, 1->lasting

            start_date = json_strs[index_1][key][0]['date']
            start_commit = json_strs[index_1][key][0]['commit_id']
            expect_operation = json_strs[index_1][key][events_num - 1]['change_operation']

            if events_num > 1 and "delete" in expect_operation:  # multi change events(max 2), end of lifetime
                end_date = json_strs[index_1][key][1]['date']
                end_commit = json_strs[index_1][key][1]['commit_id']
                end_commit_index = self.all_commits.index(end_commit)
            else:
                end_date = default_end_date
                end_commit_index = total_commits_num - 1
                lasting_mark = 1
            lasting_mark_set.append(lasting_mark)

            # days
            start_date = start_date.replace("\"", "").strip()
            end_date = end_date.replace("\"", "").strip()
            day_delta = self.time_delta(key, start_date, end_date)
            lifetime_days.append(day_delta)

            # commits and commit based rates
            start_commit_index = self.all_commits.index(start_commit)
            commit_delta = abs(end_commit_index - start_commit_index)
            rate = format(float(commit_delta / total_commits_num * 100), '.2f')
            commit_and_rate = commit_delta.__str__() + "," + rate + "%"
            lifetime_commits.append(commit_and_rate)
        return lifetime_days, lifetime_commits, lasting_mark_set

    def time_delta(self, key, start_date, end_date):
        d1 = time.mktime(time.strptime(start_date, "%a %b %d %H:%M:%S %Y %z"))
        d2 = time.mktime(time.strptime(end_date, "%a %b %d %H:%M:%S %Y %z"))
        start = datetime.datetime.fromtimestamp(d1)
        end = datetime.datetime.fromtimestamp(d2)
        delta = abs((end - start).days)
        lifetime_str = f"{key},\"{delta}\""
        return lifetime_str
   
