import os
import re
from os.path import join
import json
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class CheckSuppressionLevels(Experiment):
    """
    Check the levels of all suppressions, especially useless suppressions
    line level suppressions has a lower possibility to accidentally suppress other warnings. 

    Requirements:
     * ComputeAccidentallySuppressedWarnings.py
    """

    def check_pylint_suppression_level(self, file_path, suppression_line_nums, is_useless_list):
        suppression_levels = {}
        for l in self.levels:
            suppression_levels.update({l: []})

        with open(file_path, 'r') as file:
            lines = file.readlines()

        for line_num, is_useless in zip(suppression_line_nums, is_useless_list):
            i = line_num - 1
            stripped_line = lines[i].strip()
            suppression_match = re.search(r'\s*pylint:\s*disable', stripped_line)
            if suppression_match:
                # Check for line-level suppressions
                if suppression_match:
                    key = None
                    if stripped_line.startswith("#"): # may block-level, including file level
                        # Check for function-level and class-level suppressions
                        start_line = lines[i-1].strip()
                        if start_line.startswith('def '):
                            key = 'function_level'
                        elif start_line.startswith('class '):
                            key = 'class_level'
                        else:
                            key = 'block_level'
                    else:
                        key = 'line_level'

                    if key:
                        suppression_levels[key].append(f"{is_useless}, {line_num}, {stripped_line}")
                        if is_useless:
                            self.all_repo_counts_useless[key] += 1
                            self.individual_repo_counts_useless[key] += 1
                            self.individual_repo_counts_useless["all"] += 1
                        
        counts = {}
        keys = suppression_levels.keys()
        for key in keys:
            c = len(suppression_levels[key])
            counts.update({key: c})
            self.individual_repo_counts[key] += c
            self.individual_repo_counts["all"] += c
            self.all_repo_counts[key] += c

        suppression_levels_in_current_file = \
                {"file_path": file_path, 
                "counts": counts,
                "suppression_levels": suppression_levels}
        
        self.individual_repo_meta.append(suppression_levels_in_current_file)

    def main(self): 
        repo_dirs = self.get_repo_dirs()
        self.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        self.all_repo_counts = {"all": 0} # overall counts for all repos
        self.individual_repo_counts = {"all": 0} # overall counts for a single repo
        self.individual_repo_meta = []

        self.all_repo_counts_useless = {"all": 0} 
        self.individual_repo_counts_useless = {"all": 0}

        self.levels = ["class_level", "function_level", "block_level", "line_level"]
        for l in self.levels:
            self.all_repo_counts.update({l: 0})
            self.individual_repo_counts.update({l: 0})
            self.all_repo_counts_useless.update({l: 0})
            self.individual_repo_counts_useless.update({l: 0})
        self.all_repo_counts.update({"detailed": []}) # to store the counts for each repo
        self.all_repo_counts_useless.update({"detailed": []}) # to store the counts for each repo

        self.run(repo_dirs)

    def run(self, repo_dirs):
        result_folder = join("data", "results")
        output_folder = join(result_folder, "suppression_levels")
        os.makedirs(output_folder, exist_ok=True)

        for repo_dir in repo_dirs:
            repo_name = repo_dir_to_name(repo_dir)
            suppressions_in_latest_commit_folder = join(result_folder, repo_name, "commits")
            latest_commit = os.listdir(suppressions_in_latest_commit_folder)[0]
            suppressions_in_latest_commit_file = join(suppressions_in_latest_commit_folder, latest_commit, "suppressions.csv")
            with open(suppressions_in_latest_commit_file, "r") as f:
                suppressions_in_latest_commit = f.readlines()

            useless_suppressions_file = join(suppressions_in_latest_commit_folder, latest_commit, "pylint_useless_suppressions.csv")
            with open(useless_suppressions_file, "r") as f:
                useless_suppressions_in_latest_commit = f.readlines()
            
            pre_file_path = suppressions_in_latest_commit[0].split(",")[0]
            suppression_line_nums = []
            is_useless_list = []
            suppression_num = len(suppressions_in_latest_commit)
            for i, line in enumerate(suppressions_in_latest_commit):
                line_splits = line.split(",")
                file_path = line_splits[0]
                line_num = int(line_splits[-1])
                if line in useless_suppressions_in_latest_commit:
                    is_useless_list.append("useless")
                else:
                    is_useless_list.append("")
                
                if i + 1 == suppression_num:
                    if file_path != pre_file_path:
                        file_contain_suppression = join(repo_dir, pre_file_path)
                        self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums, is_useless_list)
                        suppression_line_nums = []
                        is_useless_list = []
                    suppression_line_nums.append(line_num)
                    file_contain_suppression = join(repo_dir, file_path)
                    self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums, is_useless_list)
                elif file_path != pre_file_path:
                    file_contain_suppression = join(repo_dir, pre_file_path)
                    self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums, is_useless_list)
                    suppression_line_nums = []
                    is_useless_list = []
                
                suppression_line_nums.append(line_num)

                pre_file_path = file_path

            # repo level summary
            self.all_repo_counts["all"] += self.individual_repo_counts["all"]
            self.all_repo_counts_useless["all"] += self.individual_repo_counts_useless["all"]

            for key, val in self.individual_repo_counts.items():
                self.individual_repo_counts[key] = f"{self.individual_repo_counts_useless[key]}/{val}"
            self.individual_repo_meta.insert(0, self.individual_repo_counts)  
            write_counts(join(output_folder, f"{repo_name}_meta.json"), self.individual_repo_meta)
            self.all_repo_counts["detailed"].append({repo_name: self.individual_repo_counts})

            # empty the dicts to start checking for the next repo
            self.individual_repo_counts = {"all": 0}
            self.individual_repo_counts_useless = {"all": 0}
            for l in self.levels:
                self.individual_repo_counts.update({l: 0})
                self.individual_repo_counts_useless.update({l: 0})
            self.individual_repo_meta = []

        for key, val in self.individual_repo_counts.items():
            self.all_repo_counts[key] = f"{self.all_repo_counts_useless[key]}/{self.all_repo_counts[key]}"
        write_counts(join(output_folder, "overall.json"), self.all_repo_counts)

def write_counts(file, to_write):
    with open(file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)


if __name__=="__main__":
    CheckSuppressionLevels().main()