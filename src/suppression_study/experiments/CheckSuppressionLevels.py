import ast
from io import StringIO
import os
import re
from os.path import join
import json
import tokenize
from suppression_study.experiments.Experiment import Experiment
from suppression_study.utils.GitRepoUtils import repo_dir_to_name


def get_code_structure(file):
    with open(file, 'r') as file:
        source = file.read()
    
    tree = ast.parse(source)
    code_structure = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            code_structure.append((node.lineno, type(node).__name__, node.name))

    return source, sorted(code_structure, key=lambda x: x[0])

def get_first_code_line(token_lines):
    """
    Identify the first line containing actual Python code, ignoring comments and blank lines.
    """
    for token in token_lines:
        if token.type == tokenize.NAME or token.type == tokenize.STRING:
            return token.start[0]
    return None

def get_first_code_line_after(start_line, token_lines):
    """
    Find the first actual code line after a specific start line, ignoring comments and blank lines.
    """
    for token in token_lines:
        if token.start[0] > start_line and (token.type == tokenize.NAME or token.type == tokenize.STRING):
            return token.start[0]
    return None


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

        source, code_structure = get_code_structure(file_path)
        tokens = list(tokenize.generate_tokens(StringIO(source).readline))
        first_code_line = get_first_code_line(tokens)

        key = "block_level"  # Default to block-level
        for line_num, is_useless in zip(suppression_line_nums, is_useless_list):
            i = line_num - 1
            stripped_line = lines[i].strip()
            suppression_match = re.search(r'\s*pylint:\s*disable', stripped_line)
            if suppression_match:
                # Check for file-level suppression (before the first line of actual code)
                if first_code_line and line_num < first_code_line:
                    key = "file_level"
                else:
                    # Check for line-level suppressions
                    if suppression_match:
                        if not stripped_line.startswith("#"):
                            key = "line_level"
                        else:
                            # Check for class-level or function-level suppression
                            for lineno, node_type, name in code_structure:
                                first_code_line_after = get_first_code_line_after(lineno, tokens)
                                if line_num > lineno and (not first_code_line_after or line_num < first_code_line_after):
                                    if node_type == 'ClassDef':
                                        key = "class_level"
                                    elif node_type == 'FunctionDef':
                                        key = "function_level"
                                    break
           
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

        self.levels = ["file_level", "class_level", "function_level", "block_level", "line_level"]
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
                is_useless = False
                line_splits = line.split(",")
                file_path = line_splits[0]
                line_num = int(line_splits[-1])
                if line in useless_suppressions_in_latest_commit:
                    is_useless = True
                
                if i + 1 == suppression_num:
                    if file_path != pre_file_path:
                        file_contain_suppression = join(repo_dir, pre_file_path)
                        self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums, is_useless_list)
                        suppression_line_nums = []
                        is_useless_list = []
                    suppression_line_nums.append(line_num)
                    if is_useless:
                        is_useless_list.append("useless")
                    else:
                        is_useless_list.append("")
                    file_contain_suppression = join(repo_dir, file_path)
                    self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums, is_useless_list)
                    # here is the end point.
                elif file_path != pre_file_path:
                    file_contain_suppression = join(repo_dir, pre_file_path)
                    self.check_pylint_suppression_level(file_contain_suppression, suppression_line_nums, is_useless_list)
                    suppression_line_nums = []
                    is_useless_list = []
                
                suppression_line_nums.append(line_num)
                if is_useless:
                    is_useless_list.append("useless")
                else:
                    is_useless_list.append("")
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