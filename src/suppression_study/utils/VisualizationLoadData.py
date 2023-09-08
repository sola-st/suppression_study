import csv


def load_data_from_csv(csv_file):
    '''
    Load data for visualizing by columns, what this function does:
    For example: 
        If the received csv_file has
            file header = [
                "col 0",
                "col 1",
            ]
        The return data will be 
        data : dict {
            "col 0", all contents in columns 0",
            "col 1", all contents in columns 1"
        }
    '''
    
    with open(csv_file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)
        data = {col: [] for col in header}

        for row in csv_reader:
            for col, value in zip(header, row):
                data[col].append(value)

    return data