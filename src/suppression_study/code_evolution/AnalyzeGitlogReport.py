from suppression_study.code_evolution.CommitBlock import CommitBlock


class AnalyzeGitlogReport:
    def __init__(self, log_result, suppressor, raw_warning_type):
        self.log_result = log_result
        self.suppressor = suppressor
        self.raw_warning_type = raw_warning_type

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
                            commit_block, self.suppressor, self.raw_warning_type
                        ).from_commit_block_to_add_event()
                        if add_events != None:
                            return add_events
                        else:
                            commit_block = []
                            start_count = 1
                # Append lines to commit_block
                if start_count == 1:
                    commit_block.append(line)

            if line_count == lines_max:
                add_events = CommitBlock(
                    commit_block, self.suppressor, self.raw_warning_type
                ).from_commit_block_to_add_event()
                assert add_events != None  # always has an add event for all suppressions
                return add_events
