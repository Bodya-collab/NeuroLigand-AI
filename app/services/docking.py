import subprocess
import os
import sys

# Путь к Vina (проверь, что он верный)
if sys.platform == "win32":
    VINA_PATH = "app/bin/vina.exe"
else:
    VINA_PATH = "/usr/bin/vina"


def get_protein_center(pdb_file):
    """
    Читает PDB и находит центр масс (среднее X, Y, Z).
    Это нужно, чтобы не стрелять в 0,0,0.
    """
    x_coords = []
    y_coords = []
    z_coords = []

    with open(pdb_file, "r") as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                try:
                    # Координаты в PDB файле всегда на фиксированных местах
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())

                    x_coords.append(x)
                    y_coords.append(y)
                    z_coords.append(z)
                except ValueError:
                    continue

    if not x_coords:
        return 0, 0, 0  # Если файл пустой (не дай бог)

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

    # Логика прицела
    if cx == 0.0 and cy == 0.0 and cz == 0.0:
        # Авто-центр (Глупый, но переварит любой файл)
        cx, cy, cz = get_protein_center(protein_path)
        box_size = "40"
        print(f"🌍 АВТО-ЦЕНТР: Координаты {cx}, {cy}, {cz} (Коробка {box_size})")
    else:
        # Снайперский прицел (Умный)
        box_size = "20"
        print(
            f"🎯 СНАЙПЕРСКИЙ ПРИЦЕЛ: Точно в карман {cx}, {cy}, {cz} (Коробка {box_size})"
        )

    # Формируем команду
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

    print(f"🚀 Запускаю Vina...")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Vina Error: {result.stderr}")
            return None
        return output_path
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return None

    # 1. Вычисляем центр белка
    cx, cy, cz = get_protein_center(protein_path)
    print(f"🎯 АВТО-ПРИЦЕЛ: Центр белка найден в {cx}, {cy}, {cz}")

    # 2. Формируем команду
    command = [
        VINA_PATH,
        "--receptor",
        protein_path,
        "--ligand",
        ligand_path,
        "--out",
        output_path,
        # Используем найденные координаты!
        "--center_x",
        str(cx),
        "--center_y",
        str(cy),
        "--center_z",
        str(cz),
        # Размер коробки (Достаточно большой, чтобы покрыть белок)
        "--size_x",
        "50",
        "--size_y",
        "50",
        "--size_z",
        "50",
        "--exhaustiveness",
        "8",
    ]

    print(f"🚀 Запускаю Vina...")

    try:
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Vina Error: {result.stderr}")
            return None

        print("✅ Vina завершила работу успешно.")
        return output_path

    except Exception as e:
        print(f"❌ Ошибка запуска subprocess: {e}")
        return None
