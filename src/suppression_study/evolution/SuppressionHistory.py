import json
from suppression_study.evolution.ChangeEvent import ChangeEvent


class SuppressionHistory():
    # Suppression history is a sequence of change events.
    def __init__(self, history_accumulator, all_change_events_list_commit_level, history_json_file):
        self.history_accumulator = history_accumulator
        self.all_change_events_list_commit_level = all_change_events_list_commit_level
        self.history_json_file = history_json_file

    def add_unique_history_to_accumulator(self):
        if self.all_change_events_list_commit_level:
            key_continuous_int = -1 # the last number in key from history sequence
            check_index = -1 # Default value -1, as actual index can be 0.
            if self.history_accumulator:
                # Only 1 key in .key(), as a suppression has one suppression ID.
                dict_keys_to_list = list(self.history_accumulator[-1].keys())
                key_continuous_int = int(dict_keys_to_list[0].replace("# S", ""))

                # TODO: do we need this code?
                # change_events_suppression_level is always undefined,
                # and hence, there always is an exception that simply gets ignored
                try:
                    check_index = self.history_accumulator.index(change_events_suppression_level)
                except:
                    pass
            
            for suppression_level_dict in self.all_change_events_list_commit_level:
                old_key = list(suppression_level_dict.keys())[0]
                change_events_suppression_level = suppression_level_dict[old_key]
                
                if check_index == -1: # New events
                    for single_change_event in change_events_suppression_level:
                        # Totally new events
                        if str(single_change_event) not in str(self.history_accumulator):
                            key_continuous_int += 1
                            updated_key = "# S" + str(key_continuous_int)
                            updated_suppression_level_dict = {updated_key : change_events_suppression_level}
                            self.history_accumulator.append(updated_suppression_level_dict)
                            break
                        else:
                            for suppression_level_events in self.history_accumulator:
                                get_key = ""
                                if str(single_change_event) in str(suppression_level_events) \
                                        and len(change_events_suppression_level) < len(suppression_level_events):
                                    # Part new events, should update to new version
                                    for key, value in self.history_accumulator[0].items():
                                        if value == suppression_level_events:
                                            get_key = key
                                        self.history_accumulator[0][get_key] = change_events_suppression_level
                                        break 
        return self.history_accumulator
    
    # Write all extracted suppression level histories to a JSON file.
    def write_all_accumulated_histories_to_json(self):                                
        with open(self.history_json_file, "w", newline="\n") as ds:
            json.dump(self.history_accumulator, ds, indent=4, ensure_ascii=False)

    '''
    The format of all_change_events_list_commit_level:

    [ ---- commit level: the element is a suppression level dict [suppression ID : change event(s)]
        {
            "# S0": [ ---- suppression level: the element is a change event
                {
                    "commit_id": "xxxx",
                    "date": "xxx",
                    "file_path": "xxx.py",
                    "warning_type": "# pylint: disable=missing-module-docstring",
                    "line_number": 1,
                    "change_operation": "add"
                },
                {...}
            ]
        },
        {
            "# S1": [...]
        }
        ...
    ]
    '''


def read_histories_from_json(json_file):
    """ Returns a list of lists of ChangeEvents. """
    with open(json_file, "r") as f:
        raw_histories = json.load(f)

    histories = []
    for raw_history_wrapper in raw_histories:
        keys = list(raw_history_wrapper.keys())
        assert len(keys) == 1 and keys[0].startswith("# S")
        raw_history = raw_history_wrapper[keys[0]]
        
        change_events = [ChangeEvent(**raw_event) for raw_event in raw_history] 
        histories.append(change_events)
    
    return histories
