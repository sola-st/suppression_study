class SuppressionInfo():
    '''Class for representing suppression csv files'''
    def __init__(self, file_path, warning_type, line_number):
        self.file_path = file_path
        self.warning_type = warning_type
        self.line_number = line_number
