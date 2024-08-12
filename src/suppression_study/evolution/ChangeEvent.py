class ChangeEvent:
    def __init__(self, commit_id, date, file_path, warning_type, line_number, change_operation, middle_status_chain=None):
        # limit commit hash length to 8 characters so we use the same length everywhere
        self.commit_id = commit_id[:8]  
        self.date = date
        self.file_path = file_path
        self.warning_type = warning_type
        self.line_number = line_number
        self.change_operation = change_operation
        self.middle_status_chain = middle_status_chain

    def __hash__(self):
        return hash((self.commit_id, self.date, self.file_path, 
                self.warning_type, self.line_number, self.change_operation))

    def __eq__(self, __value: object) -> bool:
        return self.commit_id == __value.commit_id and self.date == __value.date \
                and self.file_path == __value.file_path and self.warning_type == __value.warning_type \
                and self.line_number == __value.line_number and self.change_operation == __value.change_operation

def get_change_event_dict(given_object):
    change_event = {
        "commit_id": given_object.commit_id,
        "date": given_object.date,
        "file_path": given_object.file_path,
        "warning_type": given_object.warning_type,
        "line_number": given_object.line_number,
        "change_operation": given_object.change_operation,
        "middle_status_chain": given_object.middle_status_chain
    }
    return change_event