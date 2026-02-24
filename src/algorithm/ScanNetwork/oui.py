import csv
from typing import Dict

def load_oui_csv(path: str) -> Dict[str, str]:
    """
    IEEE OUI CSV format:
    ['Registry','Assignment','Organization Name','Organization Address']
    Example row:
    ['MA-L','286FB9','Nokia Shanghai Bell Co., Ltd.','...']
    """
    mapping: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignment = (row.get("Assignment") or "").strip().replace("-", "").replace(":", "").upper()
            org = (row.get("Organization Name") or "").strip()
            if len(assignment) == 6 and org:
                mapping[assignment] = org
    return mapping
