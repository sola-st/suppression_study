from suppression_study.evolution.WarningTypeLine import GetWarningTypeLine, WarningTypeLine


class IdentifyChangeOperation():
    # TODO in the following docstring, clarify the meaning of these two lists (why two and not one?)
    '''
    Identify change operation for change events:
    1) file add
    2) file delete
    *) file rename(automatically done by running git log command)

    1) add
    2) delete
    3) inline add/delete
    4) tricky cases
    *) no change
    '''
    def __init__(self, commit_block):
        self.old_source_code = commit_block.old_source_code
        self.old_hunk_line_range = commit_block.old_hunk_line_range
        self.new_source_code = commit_block.new_source_code
        self.new_hunk_line_range = commit_block.new_hunk_line_range
        self.operation_helper = commit_block.operation_helper

    def identify_change_operation(self):
        type_line_set = []
        operation_set = []
        tricky_mark = False
        old_type_line_set = GetWarningTypeLine(self.old_source_code, self.old_hunk_line_range).get_warning_type_line()
        new_type_line_set = GetWarningTypeLine(self.new_source_code, self.new_hunk_line_range).get_warning_type_line()
        
        old_suppression_count = len(old_type_line_set)
        new_suppression_count = len(new_type_line_set)
        if old_suppression_count == 0: # no suppression in old commit
            if new_suppression_count > 0: 
                if self.operation_helper: # if operation_helper exists, it's a file add case.
                    operation = self.operation_helper
                else:
                    operation = "add"
                for i in range(new_suppression_count):
                    operation_set.append(operation)
                type_line_set = new_type_line_set
        else: # old_suppression_count > 0
            if new_suppression_count == 0:
                operation = "delete"
                for i in range(old_suppression_count):
                    operation_set.append(operation)
                type_line_set = old_type_line_set
            else: # suppression in both old and new commit
                if old_suppression_count == new_suppression_count: 
                    # old/new_suppression_count can be 1 or more, here count # type: ignore[A, B] as 1
                    for old, new in zip(old_type_line_set, new_type_line_set):
                        old_warning_types, new_warning_types = self.separate_multiple_warning_types(old, new)
                        old_multi_num = len(old_warning_types)
                        new_multi_num = len(new_warning_types)
                        # Get change operations, cover different inline change sub-cases
                        type_line_set, operation_set = self.identify_inline_change_operation(old_multi_num, new_multi_num, \
                                old, new, old_warning_types, new_warning_types)
                else: # Include tricky cases, and some normal delete and add cases.
                    type_line_set, operation_set, tricky_mark = self.identify_complex_change_operations(old_type_line_set, new_type_line_set)
        return type_line_set, operation_set, tricky_mark   


    def separate_multiple_warning_types(self, old, new):
        # Separate "# type: ignore[A, B]"" to "A" and "B", to handle multiple warning types in one suppression line
        old_warning_types = []
        new_warning_types = []
        if "," in old.warning_type:
            old_warning_types = old.warning_type.split(",")
        else:
            old_warning_types.append(old.warning_type)

        if "," in new.warning_type:
            new_warning_types = new.warning_type.split(",")
        else:
            new_warning_types.append(new.warning_type)
        return old_warning_types, new_warning_types

    def identify_inline_change_operation(self, old_multi_num, new_multi_num, old, new, old_warning_types, new_warning_types):
        # This function is called under condition - old_suppression_count == new_suppression_count
        # Focus on inline changes, which means the basic is 1 suppression line.
        type_line_set = []
        operation_set = []
        old_line_number = old.line_number
        new_line_number= new.line_number
        # Sub-case: the number of warnings in the line is the same, covers 0.
        if old_multi_num == new_multi_num:
            if old_multi_num == 1:
                if old.warning_type != new.warning_type:
                    operation = "delete"
                    type_line_set.append(old)
                    operation_set.append(operation)
                    operation = "add"
                    type_line_set.append(new)
                    operation_set.append(operation)
        else: # Sub-case: delete existing / add new warning types inline
            for old_type in old_warning_types:
                old_type = old_type.strip()
                if old_type not in str(new_warning_types):
                    operation = "delete"
                    type_line_set.append(WarningTypeLine(old_type, old_line_number))
                    operation_set.append(operation)
                else:
                    if old_type in new_warning_types:
                        new_warning_types.remove(old_type)
                        # An example from real projects: (mistype in source repos' code)
                        # old: ['# pylint: disable=g-import-not-at-top', 'protected-access']
                        # new: ['# pylint:disable=g-import-not-at-top', 'protected-accessk', 'import-error']
                        # protected-access

            # new_warning_types still not empty, they are newly added warning types.
            if new_warning_types:
                for new_type in new_warning_types:
                    operation = "add"
                    type_line_set.append(WarningTypeLine(new_type, new_line_number))
                    operation_set.append(operation)
        return type_line_set, operation_set

    def identify_complex_change_operations(self, old_type_line_set, new_type_line_set):
        # This function is called under condition - old_suppression_count != new_suppression_count
        type_line_set = []
        operation_set = []
        tricky_mark = False
        # Threat: Inline level, separate_multiple_warning_types : so far, ignore this part
        '''
        Heuristic ground truth to map tricky cases:
        (a 10 represents: type a line 10)
        eg,. old warning types: a 10, b 11, c 14 
                new warning types: a 10, a 11, d 16 
            expected results:
                a 10 -> a 10, no change (map the first a in new commit)
                b 11 -> deleted
                c 14 -> deleted
                a 11 -> add
                d 16 -> add
        ''' 
        for old in old_type_line_set:
            found_instances_in_old = [instance for instance in new_type_line_set if old.warning_type in instance.warning_type]
            if not found_instances_in_old: # The old warning is not in the new warning set.
                operation = "delete"
                operation_set.append(operation)
                type_line_set.append(old)
            else:
                # Always get the first one for mapping, heuristically set to 1:1
                heuristic_selected_map = found_instances_in_old[0] 
                new_type_line_set.remove(heuristic_selected_map)
                tricky_mark = True # So far, just a symbol for record tricky information, using for analyzing later

        if new_type_line_set:
            for new in new_type_line_set:
                operation = "add"
                operation_set.append(operation)
                type_line_set.append(new)
        
        return type_line_set, operation_set, tricky_mark