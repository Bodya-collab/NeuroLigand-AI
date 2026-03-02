import requests
import os
import csv
from io import StringIO
from app.services.docking import get_protein_center

# Saving coordinates, in order to prevent dependeces to API
POCKET_CACHE = {
    "1cx2": (23.477, 35.196, 2.211),  # COX-2 (Aspirin,Ibuprofen)
    "1a4w": (10.0, 20.0, 15.0),  # HIV Protease 
    "1m17": (22.5, 38.0, 14.5),  # EGFR (Gefitinib)
    "3cln": (15.0, 25.0, 10.0),  # Calmodulin (Calcium binding)
}


def get_smart_pocket(pdb_path: str):
    print("Scanning pockets ...")

    try:
        filename = os.path.basename(pdb_path)
        original_name = filename.split("_", 1)[1]
        pdb_code = original_name[:4].lower()
    except Exception:
        pdb_code = "unknown"

    print(f"Identifing protein {pdb_code.upper()}")

    # 1. Immediately return from cache if we have this protein
    if pdb_code in POCKET_CACHE:
        cx, cy, cz = POCKET_CACHE[pdb_code]
        print(f"✅ Found in cache: {cx}, {cy}, {cz}")
        return cx, cy, cz

    # 2. Test API PRANKWEB (if protein is known to them)
    try:
        csv_url = f"https://prankweb.cz/api/v2/analyze/pdb/{pdb_code}/predictions.csv"
        response = requests.get(csv_url, timeout=3)
        if response.status_code == 200:
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            top_pocket = next(reader)
            cx, cy, cz = (
                float(top_pocket["center_x"]),
                float(top_pocket["center_y"]),
                float(top_pocket["center_z"]),
            )
            print(f"Coordinates API: {cx}, {cy}, {cz}")
            return cx, cy, cz
    except Exception:
        pass

    # 3. For unknown proteins, we can try to find pockets ourselves (not very smart, but better than nothing)
    print("⚠️ Focusing on geometry radar..")
    return get_protein_center(pdb_path)
