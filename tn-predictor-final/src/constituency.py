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


class ConstituencyData:
    def __init__(self, file_path: str = "data/constituencies.json"):
        self.file_path = file_path
        self.data: Dict[str, Dict[str, Any]] = {}
        self.initial_constituency_data = [
            {"name": "Kolathur", "district": "Chennai", "key_parties": ["DMK", "AIADMK", "BJP"], "incumbent_mla": "M. K. Stalin (DMK)", "major_issues": ["Water Supply", "Sanitation", "Road Infrastructure"]},
            {"name": "Coimbatore South", "district": "Coimbatore", "key_parties": ["BJP", "MNM", "Congress"], "incumbent_mla": "Vanathi Srinivasan (BJP)", "major_issues": ["Industrial Development", "Pollution Control", "Public Transport"]},
            {"name": "Edappadi", "district": "Salem", "key_parties": ["AIADMK", "DMK"], "incumbent_mla": "K. Palaniswami (AIADMK)", "major_issues": ["Agricultural Support", "Water Scarcity", "Road Connectivity"]},
            {"name": "Chepauk-Thiruvallikeni", "district": "Chennai", "key_parties": ["DMK", "AIADMK"], "incumbent_mla": "Udhayanidhi Stalin (DMK)", "major_issues": ["Urban Redevelopment", "Traffic Management", "Public Amenities"]},
            {"name": "Bodinayakanur", "district": "Theni", "key_parties": ["AIADMK", "DMK"], "incumbent_mla": "O. Panneerselvam (AIADMK)", "major_issues": ["Water Management", "Agricultural Pricing", "Textile Industry Support"]},
        ]
        self.load_data()

    def load_data(self):
        loaded_data = load_json(self.file_path)
        if loaded_data:
            if isinstance(loaded_data, list):
                self.data = flatten_dict_list(loaded_data, 'name')
                print(f"Loaded {len(self.data)} constituencies from {self.file_path} (converted from list).")
            elif isinstance(loaded_data, dict):
                self.data = loaded_data
                print(f"Loaded {len(self.data)} constituencies from {self.file_path} (as dict).")
            else:
                print(f"Warning: Invalid data format in {self.file_path}. Using empty data.")
                self.data = {}
        else:
            print(f"'{self.file_path}' not found or empty. Using initial dummy data and saving.")
            self.data = flatten_dict_list(self.initial_constituency_data, 'name')
            self.save_data()

    def save_data(self):
        data_to_save = unflatten_dict(self.data)
        save_json(self.file_path, data_to_save)
        print(f"Constituency data saved to {self.file_path}.")

    def get_all_constituencies(self) -> List[Dict[str, Any]]:
        return list(self.data.values())

    def get_all_constituency_names(self) -> List[str]:
        return list(self.data.keys())

    def get_constituency_details(self, name: str) -> Optional[Dict[str, Any]]:
        return self.data.get(name)

    def add_constituency(self, name: str, district: str, key_parties: List[str], incumbent_mla: str = "", major_issues: List[str] = []) -> bool:
        if not name or not district:
            print("Error: Constituency name and district are required.")
            return False
        if name in self.data:
            print(f"Constituency '{name}' already exists.")
            return False
        new_constituency = {"name": name, "district": district, "key_parties": key_parties, "incumbent_mla": incumbent_mla if incumbent_mla else "N/A", "major_issues": major_issues}
        self.data[name] = new_constituency
        print(f"Added constituency: {name} ({district})")
        return True

    def update_constituency(self, name: str, district: Optional[str] = None, key_parties: Optional[List[str]] = None, incumbent_mla: Optional[str] = None, major_issues: Optional[List[str]] = None) -> bool:
        if name not in self.data:
            print(f"Constituency '{name}' not found.")
            return False
        updated = False
        if district is not None:
            self.data[name]['district'] = district
            updated = True
        if key_parties is not None:
            self.data[name]['key_parties'] = key_parties
            updated = True
        if incumbent_mla is not None:
            self.data[name]['incumbent_mla'] = incumbent_mla
            updated = True
        if major_issues is not None:
            self.data[name]['major_issues'] = major_issues
            updated = True
        if updated:
            print(f"Updated details for constituency: {name}")
            return True
        else:
            print(f"No updates provided for constituency: {name}")
            return False

    def remove_constituency(self, name: str) -> bool:
        if name in self.data:
            del self.data[name]
            print(f"Removed constituency: {name}")
            return True
        else:
            print(f"Constituency '{name}' not found for removal.")
            return False
