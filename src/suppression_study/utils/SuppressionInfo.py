import csv
import os


class SuppressionInfo():
    def __init__(self, specified_commit, suppression_csv):
        self.specified_commit = specified_commit
        self.suppression_csv = suppression_csv

    def read_suppression_files(self):
        '''Read the all_suppression_commit_level, and return a list of suppression instances'''
        if not os.path.exists(self.suppression_csv):
            return 

        suppression_commit_level = []
        with open(self.suppression_csv, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for column in reader:
                file_path = column[0]
                warning_type = column[1]
                line_number = int(column[2])
                suppression_info = SuppressionInfoHelper(file_path, warning_type, line_number)
                suppression_commit_level.append(suppression_info)
        return suppression_commit_level
    

class SuppressionInfoHelper():
    '''Class for representing a single suppression'''
    def __init__(self, file_path, warning_type, line_number):
        self.file_path = file_path
        self.warning_type = warning_type
        self.line_number = line_number
