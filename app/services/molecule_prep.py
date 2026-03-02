import os
from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation


def convert_smiles_to_pdbqt(smiles: str, output_path: str):
    """
    Convert SMILES in 3D PDBQT for Vina.
    Uses RDKit for 3D geometry and Meeko for PDBQT.
    """
    print(f"preparing molecule: {smiles}")

    # 1. Create RDKit molecule from SMILES
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError("Некорректный SMILES код")

    # 2. Add hydrogens 
    mol = Chem.AddHs(mol)

    # 3. Generate 3D coordinates
    params = AllChem.ETKDGv3()
    params.useRandomCoords = True
    try:
        AllChem.EmbedMolecule(mol, params)
    except ValueError:
        # If embedding fails, we can try again with different parameters
        print("⚠️ Ошибка 3D генерации, пробуем снова...")
        AllChem.EmbedMolecule(mol)

    # 4. Minimize the molecule to get a more realistic conformation
    try:
        AllChem.MMFFOptimizeMolecule(mol)
    except Exception as e:
        print(f"⚠️ MMFF optimization error: {e}")

    # 5. Convert to PDBQT through the Meeko
    preparator = MoleculePreparation()
    preparator.prepare(mol)

    # Getting PDBQT
    pdbqt_string = preparator.write_pdbqt_string()

    # 6. Saving to file
    with open(output_path, "w") as f:
        f.write(pdbqt_string)

    print(f"Molecule prepared: {output_path}")
    return output_path
