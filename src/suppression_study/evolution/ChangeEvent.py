class ChangeEvent():
    def __init__(self, commit_id, date, file_path, warning_type, line_number, change_operation):
        self.commit_id = commit_id
        self.date = date
        self.file_path = file_path
        self.warning_type = warning_type
        self.line_number = line_number
        self.change_operation = change_operation

    def get_change_event_dict(self):
        change_event = {
            "commit_id" : self.commit_id,
            "date" : self.date,
            "file_path" : self.file_path,
            "warning_type" : self.warning_type,
            "line_number" : self.line_number,
            "change_operation" : self.change_operation,
        }
        # change_event_instance = ChangeEventHelper(change_event)
        # return change_event_instance
        return change_event
    


# class ChangeEventHelper():
#     def __init__(self, change_event):
#         for key, value in change_event.items():
#             setattr(self, key, value)