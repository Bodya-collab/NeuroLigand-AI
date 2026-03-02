from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski


def analyze_lipinski(smiles: str):
    print(f"💊 [Фармакокинетика] Анализ молекулы: {smiles}")

    try:
        # Превращаем текст (SMILES) в химический объект RDKit
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return {"error": "Неверный формат SMILES"}

        # Высчитываем 4 золотых правила
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = Lipinski.NumHDonors(mol)
        hba = Lipinski.NumHAcceptors(mol)

        # Считаем нарушения
        violations = 0
        if mw > 500:
            violations += 1
        if logp > 5:
            violations += 1
        if hbd > 5:
            violations += 1
        if hba > 10:
            violations += 1

        # Лекарство считается нормальным, если нарушений <= 1
        is_druglike = violations <= 1

        return {
            "mw": round(mw, 2),
            "logp": round(logp, 2),
            "hbd": hbd,
            "hba": hba,
            "violations": violations,
            "is_druglike": is_druglike,
        }
    except Exception as e:
        return {"error": str(e)}
