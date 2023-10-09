import json
from suppression_study.code_evolution.CommitBlock import CommitBlock


class AnalyzeGitlogReport:
    def __init__(self, log_result, suppressor, raw_warning_type, current_file):
        self.log_result = log_result
        self.suppressor = suppressor
        self.raw_warning_type = raw_warning_type
        self.current_file = current_file

    def from_gitlog_results_to_change_events(self):
        '''
        Read git log results files, get commit blocks, and represent these commit blocks to change events.
        Return a list of change events at the commit level.

        An example of how information are recorded in log_result, which is defined as commit_block:
            commit b8bxxx38xxx73533f98784700xx656b1780d
            Author: xxx xxx
            Date:   Tue Jul 4 10:50:41 2023 +0200

                <commit comment>

            diff --git a/foo.py b/foo.py
            --- /dev/null
            +++ b/foo.py
            @@ -0,0 +1,2 @@
            +def some_fun(a, b):
            +    return a + b
            \ No newline at end of file
        A 'git log' result contains one or more commit block(s).
        '''
        commit_block = []
        lines = self.log_result.split("\n")
        # if the changes before merge commit is not related to the suppression,
        # the current merge commit can be the first commit that introduces the suppression
        backup_add_events = ""

        start_count = 0
        lines_len = len(lines)
        lines_max = lines_len - 1
        for line, line_count in zip(lines, range(lines_len)):  # There are empty lines in "lines"
            line = line.replace("\n", "").strip()
            if line:
                if line.startswith("commit "):
                    start_count += 1  # found the start point of a commit_block
                    if start_count == 2:  # basic setting: one commit block has one start
                        add_events = CommitBlock(
                            commit_block, self.suppressor, self.raw_warning_type, self.current_file
                        ).from_single_commit_block_to_add_event()
                        if add_events != None:
                            if len(add_events.keys()) == 6: # not merge commit
                                return add_events
                            else:
                                add_events.pop("backup")
                                backup_add_events = add_events
                        else:
                            commit_block = []
                            start_count = 1
                # Append lines to commit_block
                if start_count == 1:
                    commit_block.append(line)

            if line_count == lines_max: # the last(oldest) commit block of current git log history results
                last_commit_block_mark = True
                add_events = CommitBlock(
                    commit_block, self.suppressor, self.raw_warning_type, self.current_file
                ).from_single_commit_block_to_add_event(last_commit_block_mark)
                if add_events == None:
                   add_events =  backup_add_events
                
                assert add_events != None  # always has an add event for all suppressions
                assert add_events != ""
                return add_events
