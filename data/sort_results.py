import os
import shutil

# Settings
SOURCE_FOLDER = "data/temp"  # Trash
TARGET_FOLDER = "data/BEST_RESULTS"  # Send best here
ENERGY_LIMIT = -7.0  # Conditions


def sort_docking_results():
    # 1. Create folder for elite if not exists
    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
        print(f"Done {TARGET_FOLDER}")

    # 2. Verifying source folder
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Error {SOURCE_FOLDER} does not exist.")
        return

    files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".pdbqt")]
    print(f"Found {len(files)} docking results in {SOURCE_FOLDER}.")

    moved_count = 0

    for filename in files:
        full_path = os.path.join(SOURCE_FOLDER, filename)

        try:
            # 3. Open and read the file to find energy
            with open(full_path, "r") as f:
                lines = f.readlines()

            energy = None
            for line in lines:
                if "REMARK VINA RESULT:" in line:
                    parts = line.split()
                    energy = float(parts[3])  # Condition: -8.5
                    break

            # 4. Deciding to move or not
            if energy is not None:
                if energy <= ENERGY_LIMIT:
                    # Move
                    new_path = os.path.join(TARGET_FOLDER, filename)
                    shutil.move(full_path, new_path)
                    print(f" {filename} (Energy: {energy}) -> Moved {TARGET_FOLDER}")
                    moved_count += 1
                else:
                    print(f" {filename} (Energy: {energy}) -> Nothing to do.")
            else:
                print(f" {filename} -> Can't find energy.")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("-" * 30)
    print(f"Decided: {moved_count} files moved to '{TARGET_FOLDER}'.")


if __name__ == "__main__":
    sort_docking_results()
