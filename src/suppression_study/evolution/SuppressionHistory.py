import json
from suppression_study.evolution.ChangeEvent import ChangeEvent, get_change_event_dict


class SuppressionHistory():
    # Suppression history is a sequence of change events.
    def __init__(self, history_accumulator, all_change_events_list_commit_level, history_json_file):
        self.history_accumulator = history_accumulator
        self.all_change_events_list_commit_level = all_change_events_list_commit_level
        self.history_json_file = history_json_file
        self.history_accumulator_list = []

    def add_unique_history_to_accumulator(self):
        if self.all_change_events_list_commit_level:
            key_continuous_int = -1 # the last number in key from history sequence
            if self.history_accumulator:
                # Only 1 key in .key(), as a suppression has one suppression ID.
                last_key = list(self.history_accumulator)[-1]
                key_continuous_int = int(last_key.replace("# S", ""))
            
            for key, change_events_suppression_level in self.all_change_events_list_commit_level.items():
                # Current change_events_suppression_level is not in history_accumulator
                # New events: 2 categories
                exists_in_accumulator = False
                start_change_event = change_events_suppression_level[0]
                update_key = None
                for key, suppression_level_change_events in self.history_accumulator.items():
                    for change_event in suppression_level_change_events:
                        # Expected: if exists, should be equals to add change event
                        if change_event == start_change_event:
                            exists_in_accumulator = True
                            update_key = key
                            break

                if exists_in_accumulator == False: # 1. Totally new events
                    key_continuous_int += 1
                    update_key = "# S" + str(key_continuous_int)
                    self.history_accumulator[update_key] = change_events_suppression_level
                else: # 2. Part new events, should update to new version if needed
                    if update_key:
                        found_suppression_level_events = self.history_accumulator[update_key]
                        if len(change_events_suppression_level) > len(found_suppression_level_events):
                            # eg,. replace only add event with add-delete events 
                            self.history_accumulator.update({update_key: change_events_suppression_level})
        return self.history_accumulator

    def get_history_accumulator_list(self):
        for key, value in self.history_accumulator.items():
            change_events_list = []
            for change_event_object in value:
                change_events_dict = get_change_event_dict(change_event_object) 
                change_events_list.append(change_events_dict)
            self.history_accumulator_list.append({key: change_events_list})

    def sort_by_date(self):

        self.history_accumulator_list.sort(key=lambda x: x[list(x.keys())[0]][0]["date"])
        for idx, x in enumerate(self.history_accumulator_list):
            assert len(x) == 1
            old_suppression_id = list(x.keys())[0]
            new_suppression_id = "# S" + str(idx)
            val = x[old_suppression_id]
            x.clear()
            x[new_suppression_id] = val

    # Write all extracted suppression level histories to a JSON file.
    def write_all_accumulated_histories_to_json(self):  
        with open(self.history_json_file, "w", newline="\n") as ds:
            json.dump(self.history_accumulator_list, ds, indent=4, ensure_ascii=False)

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