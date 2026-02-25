import os
from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation

# Убрали лишний импорт, который вызывал ошибку


def convert_smiles_to_pdbqt(smiles: str, output_path: str):
    """
    Превращает SMILES в 3D PDBQT для Vina.
    Использует RDKit для геометрии и Meeko для PDBQT.
    """
    print(f"🧪 Готовлю молекулу: {smiles}")

    # 1. Создаем молекулу из текста
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError("Некорректный SMILES код")

    # 2. Добавляем водороды (обязательно для докинга)
    mol = Chem.AddHs(mol)

    # 3. Генерируем 3D координаты
    # Использование random seed и параметров помогает создать "честную" структуру
    params = AllChem.ETKDGv3()
    params.useRandomCoords = True
    try:
        AllChem.EmbedMolecule(mol, params)
    except ValueError:
        # Если не вышло с первого раза, пробуем более простой метод
        AllChem.EmbedMolecule(mol)

    # 4. Минимизация энергии (Расправляем молекулу)
    # Это превратит "смятое кольцо" в нормальную 3D форму
    try:
        AllChem.MMFFOptimizeMolecule(mol)
    except Exception as e:
        print(f"⚠️ Ошибка оптимизации MMFF (не критично): {e}")

    # 5. Конвертация в PDBQT через Meeko
    # Meeko сам найдет вращающиеся связи и настроит PDBQT
    preparator = MoleculePreparation()
    preparator.prepare(mol)

    # Получаем строку PDBQT
    pdbqt_string = preparator.write_pdbqt_string()

    # 6. Сохраняем файл
    with open(output_path, "w") as f:
        f.write(pdbqt_string)

    print(f"✅ Молекула сохранена: {output_path}")
    return output_path
