import math


def calculate_h_bonds(protein_path: str, ligand_path: str, max_dist: float = 3.5):
    print("Radar:scanning for H-bonds...")

    def get_atoms(path, is_protein=True):
        atoms = []
        with open(path, "r") as f:
            for line in f:
                # 🛑 Killing shados
                if not is_protein and line.startswith("MODEL 2"):
                    break

                if line.startswith("ATOM") or line.startswith("HETATM"):
                    try:
                        x = float(line[30:38].strip())
                        y = float(line[38:46].strip())
                        z = float(line[46:54].strip())
                        element = line[76:78].strip().upper()
                        if not element:
                            element = line[12:16].strip()[0].upper()

                        atom_name = line[12:16].strip()
                        res_name = line[17:20].strip() if is_protein else "LIG"
                        res_num = line[22:26].strip() if is_protein else ""
                        chain = line[21] if is_protein and len(line) > 21 else ""

                        if element in ["N", "O", "F"]:
                            atoms.append(
                                {
                                    "x": x,
                                    "y": y,
                                    "z": z,
                                    "res_name": res_name,
                                    "res_num": res_num,
                                    "atom_name": atom_name,
                                    "chain": chain,
                                }
                            )
                    except:
                        pass
        return atoms

    prot_atoms = get_atoms(protein_path, is_protein=True)
    lig_atoms = get_atoms(ligand_path, is_protein=False)

    bonds = []
    for p in prot_atoms:
        for l in lig_atoms:
            dist = math.sqrt(
                (p["x"] - l["x"]) ** 2 + (p["y"] - l["y"]) ** 2 + (p["z"] - l["z"]) ** 2
            )
            if 1.5 < dist <= max_dist:
                bonds.append(
                    {
                        "start": p,
                        "end": l,
                        "distance": round(dist, 2),
                        "label": f"{p['res_name']}-{p['res_num']} (Chain {p['chain']})",
                    }
                )

    bonds = sorted(bonds, key=lambda x: x["distance"])
    return bonds[:8]
