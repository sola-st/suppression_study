import os
import re
from os.path import join
import json
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


class CheckSuppressionLevels(Experiment):
    def check_pylint_suppression_level(self, file_path, suppression_line_nums):
        suppression_levels = {}
        for l in self.levels:
            suppression_levels.update({l: []})

        with open(file_path, 'r') as file:
            lines = file.readlines()

        for line_num in suppression_line_nums:
            i = line_num - 1
            stripped_line = lines[i].strip()
            suppression_match = re.search(r'\s*pylint:\s*disable', stripped_line)
            if suppression_match:
                # Check for line-level suppressions
                if suppression_match:
                    if stripped_line.startswith("#"): # may block-level, including file level
                        # Check for function-level and class-level suppressions
                        start_line_1 = lines[i+1].strip()
                        start_line_2 = lines[i-1].strip()

                        if start_line_1.startswith('def ') or start_line_2.startswith('def '):
                            suppression_levels['function_level'].append(f"{line_num}, {stripped_line}")
                        elif start_line_1.startswith('class ') or start_line_2.startswith('class '):
                            suppression_levels['class_level'].append(f"{line_num}, {stripped_line}")
                        else:
                            suppression_levels['block_level'].append(f"{line_num}, {stripped_line}")
                    else: # line level
                        suppression_levels['line_level'].append(f"{line_num}, {stripped_line}")

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
        # self.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        self.all_repo_counts = {"all": 0} # overall counts for all repos
        self.individual_repo_counts = {"all": 0} # overall counts for a single repo
        self.individual_repo_meta = []

        self.levels = ["class_level", "function_level", "block_level", "line_level"]
        for l in self.levels:
            self.all_repo_counts.update({l: 0})
            self.individual_repo_counts.update({l: 0})
        self.all_repo_counts.update({"detailed": []}) # to store the counts for each repo

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
            
            pre_file_path = suppressions_in_latest_commit[0].split(",")[0]
            suppression_line_nums = []
            suppression_num = len(suppressions_in_latest_commit)
            for i, line in enumerate(suppressions_in_latest_commit):
                line_splits = line.split(",")
                file_path = line_splits[0]
                line_num = int(line_splits[-1])
                
                if i + 1 == suppression_num:
                    if file_path != pre_file_path:
                        file_contain_suppression = join(repo_dir, pre_file_path)
                        self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums)
                        suppression_line_nums = []
                    suppression_line_nums.append(line_num)
                    file_contain_suppression = join(repo_dir, file_path)
                    self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums)
                elif file_path != pre_file_path:
                    file_contain_suppression = join(repo_dir, pre_file_path)
                    self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums)
                    suppression_line_nums = []
                
                suppression_line_nums.append(line_num)

                pre_file_path = file_path

            self.individual_repo_meta.insert(0, self.individual_repo_counts)  
            write_counts(join(output_folder, f"{repo_name}_suppression_level_meta.json"), self.individual_repo_meta)
            self.all_repo_counts["all"] += self.individual_repo_counts["all"]
            self.all_repo_counts["detailed"].append({repo_name: self.individual_repo_counts})
            self.individual_repo_counts = {"all": 0}
            for l in self.levels:
                self.individual_repo_counts.update({l: 0})
            self.individual_repo_meta = []

        write_counts(join(output_folder, "overall_suppression_level_counts.json"), self.all_repo_counts)

def write_counts(file, to_write):
    with open(file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)


if __name__=="__main__":
    CheckSuppressionLevels().main()