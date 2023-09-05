import csv
import re


class GetLifetimeGroupsInfo:
    def __init__(self, entire_lifetime, total_commits, lifetime_output, group_output, num_groups):
        # Get lifetime groups at individual repository level
        # All the parameters here are related to current processing repository
        self.entire_lifetime = entire_lifetime
        self.total_commits = total_commits
        self.lifetime_output = lifetime_output
        self.group_output = group_output
        self.num_groups = num_groups

    def get_groups(self):
        # lifetime_output file columns=['warning_key', 'occur_days', 'occur_commits', 'commit_based_rates', 'lasting_marks']
        csv_reader = csv.reader(open(self.lifetime_output, "r"))
        data = list(csv_reader)
        occurrences_days = [row[1] for row in data]
        occurrences_commits = [row[2] for row in data]
        commit_based_rates = [row[3] for row in data]
        lasting_marks = [row[4] for row in data] # Current suppression still exists or not

        # Get groups and check if the suppression are alive
        suppression_num = occurrences_days.__len__()
        # days
        days_groups, days_groups_format = self.divide_into_groups(self.entire_lifetime)
        days_groups_num_removed, days_groups_num_lasting = self.check_suppression_if_alive(
                occurrences_days, days_groups, suppression_num, lasting_marks)

        # commits
        commits_groups, commits_groups_format = self.divide_into_groups(self.total_commits)
        commits_groups_num_removed, commits_groups_num_lasting = self.check_suppression_if_alive(
                occurrences_commits, commits_groups, suppression_num, lasting_marks)

        # rates, hard code
        rates_groups = [range(0, 2000), range(2000, 4000), range(4000, 6000), range(6000, 8000), range(8000, 10001)]
        rates_groups_format = ["[0,20%)", "[20%,40%)", "[40%,60%)", "[60%,80%)", "[80%,100%]"]
        commit_based_rates_only_digits = [int(re.sub("\D", "", rate)) for rate in commit_based_rates]
        rates_groups_num_removed, rates_groups_num_lasting = self.check_suppression_if_alive(
                commit_based_rates_only_digits, rates_groups, suppression_num, lasting_marks)

        # Write grouped results to a csv file
        to_write = ""
        for index in range(0, self.num_groups):
            day_str = f"\"{days_groups_format[index]}\",{days_groups_num_removed[index]},{days_groups_num_lasting[index]}"
            commit_str = f"\"{commits_groups_format[index]}\",{commits_groups_num_removed[index]},{commits_groups_num_lasting[index]}"
            rate_str = f"\"{rates_groups_format[index]}\",{rates_groups_num_removed[index]},{rates_groups_num_lasting[index]}"
            to_write = f"{to_write}{day_str},{commit_str},{rate_str}\n"
        
        header = (f'day_range,day_group_num_removed,day_group_num_lasting,commit_range,commit_group_num_removed,'
                f'commit_group_num_lasting,commit_based_rates_range,rate_group_num_removed,rate_group_num_lasting')
        to_write = f'{header}\n{to_write}'
        with open(self.group_output, "a") as f:
            f.write(to_write)
        print("Get groups, done.")

    def divide_into_groups(self, target):
        groups = []
        groups_format = []
        start = 0

        base_group_size = target // self.num_groups
        remainder = target % self.num_groups
        for i in range(self.num_groups):
            if i < remainder:
                group_size = base_group_size + 1
            else:
                group_size = base_group_size

            end = start + group_size

            # group : range(0, 22)
            # group_format : [0, 22)
            group = range(start, end)
            groups.append(group)

            group_format = []
            if end == target:
                group_format = f"[{start}, {end}]"
            else:
                group_format = f"[{start}, {end})"
            groups_format.append(group_format)
            start = end
        return groups, groups_format

    def check_suppression_if_alive(self, occurrences, base_groups, suppression_num, lasting_marks):
        # Given: occurrences of individual suppression (standard: days or commits)
        # Checking: if the suppression is removed or not
        # Return 2 lists of marks that show the 'remove status' of suppressions
        num_removed = [0] * self.num_groups
        num_lasting = [0] * self.num_groups

        for i in range(suppression_num):
            occr = int(occurrences[i])  # How many days/commits does current suppression alive
            for group in base_groups:
                if occr in group:
                    group_index = base_groups.index(group)
                    if lasting_marks[i] == "1":  # lasting, never removed
                        num_lasting[group_index] = num_lasting[group_index] + 1
                    else:  # Removed
                        num_removed[group_index] = num_removed[group_index] + 1
                    break
        return num_removed, num_lasting