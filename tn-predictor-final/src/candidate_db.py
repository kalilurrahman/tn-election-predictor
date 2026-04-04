import json
import os
import sys
from typing import List, Dict, Any, Optional

try:
    from utils import load_json, save_json, flatten_dict_list, unflatten_dict
except ImportError:
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    from src.utils import load_json, save_json, flatten_dict_list, unflatten_dict


class CandidateDB:
    def __init__(self, file_path: str = "data/candidates.json"):
        self.file_path = file_path
        self.data: Dict[str, Dict[str, Any]] = {}
        self.initial_candidates_data = [
            {"name": "M. K. Stalin", "party": "DMK", "constituency": "Kolathur", "status": "Active", "recent_activity": "Attended party executive meeting."},
            {"name": "K. Annamalai", "party": "BJP", "constituency": "Coimbatore South", "status": "Campaigning", "recent_activity": "Addressing rallies in Western districts."},
            {"name": "Udhyanidhi Stalin", "party": "DMK", "constituency": "Chepauk-Thiruvallikeni", "status": "Minister", "recent_activity": "Reviewing schemes related to sports and youth welfare."},
            {"name": "Kamal Haasan", "party": "MNM", "constituency": "Coimbatore South", "status": "Active", "recent_activity": "In talks for potential alliances."},
            {"name": "O. Panneerselvam", "party": "AIADMK", "constituency": "Bodinayakanur", "status": "Active", "recent_activity": "Meeting with party cadres."},
            {"name": "K. Palaniswami", "party": "AIADMK", "constituency": "Edappadi", "status": "Active", "recent_activity": "Addressing press conferences."},
        ]
        self.load_data()

    def load_data(self):
        loaded_data = load_json(self.file_path)
        if loaded_data:
            if isinstance(loaded_data, list):
                self.data = flatten_dict_list(loaded_data, 'name')
                print(f"Loaded {len(self.data)} candidates from {self.file_path} (converted from list).")
            elif isinstance(loaded_data, dict):
                self.data = loaded_data
                print(f"Loaded {len(self.data)} candidates from {self.file_path} (as dict).")
            else:
                print(f"Warning: Invalid data format in {self.file_path}. Using empty data.")
                self.data = {}
        else:
            print(f"'{self.file_path}' not found or empty. Using initial dummy data and saving.")
            self.data = flatten_dict_list(self.initial_candidates_data, 'name')
            self.save_data()

    def save_data(self):
        data_to_save = unflatten_dict(self.data)
        save_json(self.file_path, data_to_save)
        print(f"Candidate data saved to {self.file_path}.")

    def get_all_candidates(self) -> List[Dict[str, Any]]:
        return list(self.data.values())

    def get_all_candidate_names(self) -> List[str]:
        return list(self.data.keys())

    def get_candidate_details(self, name: str) -> Optional[Dict[str, Any]]:
        return self.data.get(name)

    def add_candidate(self, name: str, party: str, constituency: str, status: str = "Active", recent_activity: str = "") -> bool:
        if not name or not party or not constituency:
            print("Error: Candidate name, party, and constituency are required.")
            return False
        if name in self.data:
            print(f"Candidate '{name}' already exists.")
            return False
        new_candidate = {"name": name, "party": party, "constituency": constituency, "status": status, "recent_activity": recent_activity}
        self.data[name] = new_candidate
        print(f"Added candidate: {name}")
        return True

    def update_candidate_status_and_activity(self, name: str, new_status: str, activity_details: str) -> bool:
        if name not in self.data:
            print(f"Candidate '{name}' not found.")
            return False
        self.data[name]['status'] = new_status
        self.data[name]['recent_activity'] = activity_details
        print(f"Updated status and activity for: {name}")
        return True

    def remove_candidate(self, name: str) -> bool:
        if name in self.data:
            del self.data[name]
            print(f"Removed candidate: {name}")
            return True
        else:
            print(f"Candidate '{name}' not found for removal.")
            return False
