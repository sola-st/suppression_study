from suppression_study.evolution.WarningTypeLine import GetWarningTypeLine


class IdentifyChangeOperation():
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
    def __init__(self, old_source_code, old_hunk_line_range, new_source_code, new_hunk_line_range, operation_helper):
        self.old_source_code = old_source_code
        self.old_hunk_line_range = old_hunk_line_range
        self.new_source_code = new_source_code
        self.new_hunk_line_range = new_hunk_line_range
        self.operation_helper = operation_helper

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
                    operation_set.append(self.operation_helper)
                else:
                    operation = "add"
                    operation_set.append(operation)
                type_line_set = new_type_line_set
        else: # old_suppression_count > 0
            if new_suppression_count == 0:
                operation = "delete"
                operation_set.append(operation)
                type_line_set = old_type_line_set
            else: # suppression in both old and new commit
                if old_suppression_count == new_suppression_count: 
                    # old/new_suppression_count can be 1 or more, here count # type: ignore[A, B] as 1
                    for old, new in zip(old_type_line_set, new_type_line_set):
                        old_warning_types, new_warning_types = self.separate_multiple_warning_types(old, new)
                        old_multi_num = len(old_warning_types)
                        new_multi_num = len(new_warning_types)
                        # Get change operations, cover different in-line change sub-cases
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
        type_line_set = []
        operation_set = []
        # Sub-case: the number of warnings in a line is the same, includes 0.
        if old_multi_num == new_multi_num:
            if old.warning_type != new.warning_type:
                operation = "delete"
                type_line_set.append(old)
                operation_set.append(operation)
                operation = "add"
                type_line_set.append(new)
                operation_set.append(operation)
        # Sub-case: delete existing warning types in-line
        elif old_multi_num > new_multi_num: 
            real_delete = 0
            for old_type in old_warning_types:
                old_type = old_type.strip()
                if old_type.strip() not in str(new_warning_types):
                    real_delete +=1
                    operation = "delete"
                    type_line_set.append(old)
                    operation_set.append(operation)
            # All old warning type were deleted, and add a totally new warning type
            if real_delete == old_multi_num and new_multi_num != 0:
                for new_type in new_warning_types:
                    operation = "add"
                    type_line_set.append(new)
                    operation_set.append(operation)
        # Sub-case: add new warning types in-line
        elif old_multi_num < new_multi_num: 
            real_add = 0
            for new_type in new_warning_types:
                new_type = new_type.strip()
                if new_type.strip() not in str(old_warning_types):
                    real_add +=1
                    operation = "add"
                    type_line_set.append(new)
                    operation_set.append(operation)
            # All new warning type are newly added, and the existing warning types were deleted
            if real_add == new_multi_num and old_multi_num != 0:
                for old_type in old_warning_types:
                    operation = "delete"
                    type_line_set.append(old)
                    operation_set.append(operation)
        return type_line_set, operation_set
    
    def identify_complex_change_operations(self, old_type_line_set, new_type_line_set):
        # This function is called under condition - old_suppression_count != new_suppression_count
        type_line_set = []
        operation_set = []
        old_suppression_in_new = []
        new_suppression_in_old = []
        tricky_mark = False
        for old in old_type_line_set:
            # if old.warning_type not in str(new_type_line_set): 
            found_instances_in_old = [instance for instance in new_type_line_set if old.warning_type in instance.warning_type]
            if found_instances_in_old:
                # If an old suppression in new suppressions:
                # 1) no change to this suppression
                # 2) tricky cases, 
                # eg,. delete an old suppression with type A, 
                #      add a new suppression(type A) for different code in the same changed hunk
                operation = "delete"
                operation_set.append(operation)
                type_line_set.append(old)
            else:
                old_suppression_in_new.append(old)

        for new in new_type_line_set:
            if new.warning_type not in str(old_type_line_set): 
                operation = "add"
                operation_set.append(operation)
                type_line_set.append(new)
            else:
                new_suppression_in_old.append(new)
            
        if old_suppression_in_new or new_suppression_in_old:
            old_in_new_num = len(old_suppression_in_new)
            new_in_old_num = len(new_suppression_in_old)
            if old_in_new_num != new_in_old_num:
                # If ==, these are some unchanged suppressions
                heuristic_no_change_num = min(old_in_new_num, new_in_old_num)
                heuristic_changed_num = old_in_new_num - new_in_old_num
                if heuristic_changed_num > 0:
                    for i in range(heuristic_no_change_num, old_in_new_num):
                        operation = "delete"
                        operation_set.append(operation)
                        type_line_set.append(old_suppression_in_new[i])
                else:
                    for i in range(heuristic_no_change_num, new_in_old_num):
                        operation = "add"
                        operation_set.append(operation)
                        type_line_set.append(new_suppression_in_old[i])

                tricky_mark = True

        return type_line_set, operation_set, tricky_mark