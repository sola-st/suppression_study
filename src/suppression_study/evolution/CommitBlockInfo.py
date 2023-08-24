class CommitBlock():
    def __init__(self, commit_block):
        self. commit_block = commit_block

    def get_commit_block(self):
        '''
        Represent git log results(commit_block) to dict, 
        and then pass it to helper class to get the instance
        '''
        commit_id = ""
        date = ""
        file_path = ""
        after_line_range_mark = ""
        old_hunk_line_range = []
        new_hunk_line_range = []
        old_source_code = []
        new_source_code = []
        operation_helper = ""
        for line in self.commit_block:
            # Extract metadata from commit_block
            if line.startswith("commit "): # Commit
                commit_id = line.split(" ")[1].strip()
            elif line.startswith("Date:"): # Date
                date = line.split(":", 1)[1].strip()
            elif line.startswith("--- /dev/null"): # File not exists in old commit
                operation_helper = "file add" # Only able to report "file add", not "file delete"
            elif line.startswith("+++"): # File path in new commit
                file_path = line.split("/", 1)[1].strip()
            elif line.startswith("@@ "): # Changed hunk
                '''
                Assume 'ab' means 'absolute value of the number of changed lines'
                Format: @@ -old_start,ab +new_start,ab @@
                        eg,. @@ -1,2 +2,1 @@
                            @@ -7,2 +7,2 @@  
                Here the line number start from 1, and 0 means no lines.
                ''' 
                tmp = line.split(" ")
                old_line_tmp = tmp[1].replace("-", "").split(",")
                old_start = int(old_line_tmp[0])
                old_end = old_start + int(old_line_tmp[1])
                old_hunk_line_range = range(old_start, old_end)

                new_line_tmp = tmp[2].replace("+", "").split(",")
                new_start = int(new_line_tmp[0])
                new_end = new_start + int(new_line_tmp[1])
                new_hunk_line_range = range(new_start, new_end)
                after_line_range_mark = "yes"
            
            if after_line_range_mark: # Source code
                if line.startswith("-"):
                    old_source_code.append(line.replace("-", "", 1).strip())
                if line.startswith("+"):
                    new_source_code.append(line.replace("+", "", 1).strip())

        commit_block_dict = {
            "commit_id" : commit_id,
            "date" : date,
            "file_path" : file_path,
            "old_hunk_line_range" : old_hunk_line_range,
            "new_hunk_line_range" : new_hunk_line_range,
            "old_source_code" : old_source_code,
            "new_source_code" : new_source_code,
            "operation_helper" : operation_helper,
        }

        commit_block_instance = CommitBlockHelper(commit_block_dict)
        return commit_block_instance


class CommitBlockHelper():
    def __init__(self, commit_block_dict):
        for key, value in commit_block_dict.items():
            setattr(self, key, value)


class AllCommitBlock():
    def __init__(self, all_commit_block_file_level, file_delete_check):
        # All commit_block extracted from git log results -- commit level
        # Here, the file level exactly related to the file_delete_check
        # eg,. file level: src/main/a.py
        #      file_delete_check: main/a
        self.block = all_commit_block_file_level
        self.delete_check = file_delete_check
       