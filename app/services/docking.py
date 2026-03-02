import subprocess
import os
import sys

# Path to Vina 
if sys.platform == "win32":
    VINA_PATH = "app/bin/vina.exe"
else:
    VINA_PATH = "/usr/bin/vina"


def get_protein_center(pdb_file):
    """
    Read the PDB (median X, Y, Z).
    """
    x_coords = []
    y_coords = []
    z_coords = []

    with open(pdb_file, "r") as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                try:
                    # Coordinates are in fixed columns in PDB format
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())

                    x_coords.append(x)
                    y_coords.append(y)
                    z_coords.append(z)
                except ValueError:
                    continue

    if not x_coords:
        return 0, 0, 0  # If no atoms found, return origin

    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    center_z = sum(z_coords) / len(z_coords)

    return round(center_x, 3), round(center_y, 3), round(center_z, 3)


def run_docking(
    protein_path: str,
    ligand_path: str,
    cx: float = 0.0,
    cy: float = 0.0,
    cz: float = 0.0,
):
    output_path = ligand_path.replace("ligand", "docked_result")

    # Shooting at the pocket 
    if cx == 0.0 and cy == 0.0 and cz == 0.0:
        # Auto-center (Blind docking)
        cx, cy, cz = get_protein_center(protein_path)
        box_size = "40"
        print(f"Auto-center {cx}, {cy}, {cz} (Box {box_size})")
    else:
        # Shot
        box_size = "20"
        print(
            f"Firing at {cx}, {cy}, {cz} (Box {box_size})"
        )

    # Formating command for Vina
    command = [
        VINA_PATH,
        "--receptor",
        protein_path,
        "--ligand",
        ligand_path,
        "--out",
        output_path,
        "--center_x",
        str(cx),
        "--center_y",
        str(cy),
        "--center_z",
        str(cz),
        "--size_x",
        box_size,
        "--size_y",
        box_size,
        "--size_z",
        box_size,
        "--exhaustiveness",
        "8",
    ]

    print(f"Starting Vina with command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f" Vina Error: {result.stderr}")
            return None
        return output_path
    except Exception as e:
        print(f" Error running Vina: {e}")
        return None

    # 1. Calculating the center of the protein 
    cx, cy, cz = get_protein_center(protein_path)
    print(f"Center of protein: {cx}, {cy}, {cz}")

    # 2. Forming new command 
    command = [
        VINA_PATH,
        "--receptor",
        protein_path,
        "--ligand",
        ligand_path,
        "--out",
        output_path,
        "--center_x",
        str(cx),
        "--center_y",
        str(cy),
        "--center_z",
        str(cz),
        "--size_x",
        "50",
        "--size_y",
        "50",
        "--size_z",
        "50",
        "--exhaustiveness",
        "8",
    ]

    print(f"Starting Vina with command: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print(f" Vina Error: {result.stderr}")
            return None

        print(" Vina docking completed successfully.")
        return output_path

    except Exception as e:
        print(f" Error running subprocess: {e}")
        return None
