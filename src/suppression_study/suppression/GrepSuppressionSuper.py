import subprocess
from git.repo import Repo
import os


class GrepSuppressionSuper():

    def find_suppression(self, target_folder, raw_suppression_results):
        '''
        Run "Grep" command to find suppression
        '''
        os.chdir(target_folder) 
        # Record relative path in results
        find_command = "find . -name " + self.source_file_extension + " | xargs grep -E " + self.filter_keywords + " -n"
        result = subprocess.run(find_command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        output_txt_lines = result.stdout # output_txt_lines : type: str
        '''
        In some cases, grep command does not show file_path in the results, as only 1 file related to searching keyword.
        If so, run the command with option "-l" to get the file_path, and update the result raw_suppression_results file.
        '''
        new_txt_lines = []
        if output_txt_lines.split(":", 1)[0].isdigit():
            command = "find . -name " + self.source_file_extension + " | xargs grep -l -E " + self.filter_keywords + " -n"
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
            file_path = result.stdout.strip() # should only with a file path
            output_txt_lines_list = output_txt_lines.strip().split("\n")
            for txt in output_txt_lines_list:
                new_txt = file_path + ":" + txt
                new_txt_lines.append(new_txt)

            with open(raw_suppression_results, "w") as f:
                write_str = ""
                for line in new_txt_lines:
                    write_str = write_str + line + "\n"
                f.write(write_str)
        else:
            with open(raw_suppression_results, "w") as f:
                f.writelines(output_txt_lines)

    def grep_suppression_for_specific_commit(self):
        repo_base= Repo(self.repo_dir)
        repo_base.git.checkout(self.commit_id)
        target_folder = self.repo_dir.replace(self.repo_name, self.commit_id)
        os.rename(self.repo_dir, target_folder) # Rename, will rename back later
        
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        
        raw_suppression_results = self.output_path + self.commit_id + ".txt"
        self.find_suppression(target_folder, raw_suppression_results)
        os.rename(target_folder, self.repo_dir) # Rename back

        return raw_suppression_results

    def grep_suppression_for_all_commits(self):
        output_txt_files = []
        previous_target_folder = self.repo_dir

        all_commits = []
        with open(self.commit_id, "r") as f: # 2 columns: commit and date
            commit = f.readline().split(",")[0].replace("\"", "").strip()
            all_commits.append(commit)
        
        repo_base= Repo(self.repo_dir)
        for commit in all_commits:
            repo_base.git.checkout(commit)
            target_folder = self.repo_dir.replace(self.repo_name, commit)
            os.rename(previous_target_folder, target_folder) 
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)

            raw_suppression_results = self.output_path + commit + ".txt"
            self.find_suppression(target_folder, raw_suppression_results)
            output_txt_files.append(raw_suppression_results)
            previous_target_folder = target_folder

        os.rename(target_folder, self.repo_dir) # Rename back

        return output_txt_files
