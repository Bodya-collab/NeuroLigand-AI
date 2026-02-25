from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import os
import uuid
from app.services.molecule_prep import convert_smiles_to_pdbqt
from app.services.docking import run_docking
from app.database import get_db
from app import models

router = APIRouter()

os.makedirs("data/uploaded", exist_ok=True)
os.makedirs("data/temp", exist_ok=True)


@router.post("/dock-molecule")
async def dock_molecule(
    smiles: str = Form(...),
    center_x: float = Form(0.0),
    center_y: float = Form(0.0),
    center_z: float = Form(0.0),
    protein_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ... весь остальной код остается без изменений ...
    print(f"🔵 [1/6] Запрос: {smiles}")
    job_id = str(uuid.uuid4())[:8]

    # Пути для файлов
    protein_pdb_path = f"data/uploaded/{job_id}_{protein_file.filename}"
    protein_pdbqt_path = f"data/temp/{job_id}_protein.pdbqt"

    # 1. ЧИСТИМ И СОЗДАЕМ PDBQT БЕЛКА (ИСПРАВЛЕНИЕ ФИЗИКИ)
    content = await protein_file.read()
    lines = content.decode("utf-8").splitlines()

    with open(protein_pdb_path, "w", encoding="utf-8") as f_pdb, open(
        protein_pdbqt_path, "w", encoding="utf-8"
    ) as f_pdbqt:
        for line in lines:
            if line.startswith("ATOM"):
                # Сохраняем обычный PDB для красивой картинки на сайте
                f_pdb.write(line + "\n")

                # --- МАГИЯ PDBQT ---
                base = line[:54]  # Забираем координаты
                atom_name = line[12:16].strip()
                res_name = line[17:20].strip()

                # Угадываем AutoDock тип атома
                if "C" in atom_name:
                    ad_type = "A" if res_name in ["PHE", "TYR", "TRP", "HIS"] else "C"
                elif "O" in atom_name:
                    ad_type = "OA"
                elif "N" in atom_name:
                    ad_type = "N"
                elif "S" in atom_name:
                    ad_type = "SA"
                else:
                    ad_type = atom_name[0]

                # Формируем строку: база + 16 пробелов + заряд 0.000 + тип атома
                # База(54) + Оккупация(6) + Темп(6) + Отступ(4) + Заряд(6) + Отступ(1) + Тип(2)
                pdbqt_line = f"{base:<54}  1.00  0.00     0.000 {ad_type:<2}\n"
                f_pdbqt.write(pdbqt_line)

    print(f"🔵 [2/6] Белок сконвертирован в PDBQT!")

    # 2. База данных
    new_job = models.Job(ligand_smiles=smiles, status="processing")
    project = db.query(models.Project).first()
    if not project:
        project = models.Project(
            name="Demo Project", protein_filename=protein_file.filename
        )
        db.add(project)
        db.commit()
    new_job.project_id = project.id
    db.add(new_job)
    db.commit()

    try:
        # 3. Готовим лиганд
        print("🔵 [3/6] Генерация 3D лиганда...")
        ligand_path = f"data/temp/{job_id}_ligand.pdbqt"
        convert_smiles_to_pdbqt(smiles, ligand_path)
        print("🔵 [4/6] Лиганд готов. Запускаем Vina...")

        # 4. Запускаем Докинг (ПЕРЕДАЕМ ПРАВИЛЬНЫЙ PDBQT БЕЛОК!)
        result_path = run_docking(
            protein_pdbqt_path, ligand_path, center_x, center_y, center_z
        )
        print("🔵 [5/6] Vina завершила работу!")

        # 5. Парсим результат
        affinity = None
        if result_path and os.path.exists(result_path):
            with open(result_path, "r") as f:
                for line in f:
                    if "REMARK VINA RESULT:" in line:
                        affinity = float(line.split()[3])
                        break

        print(f"🔵 [6/6] Энергия: {affinity}")

        if affinity is not None:
            new_job.status = "completed"
            new_job.result_affinity = affinity
            db.commit()
            return {
                "status": "success",
                "message": "Docking Completed Successfully!",
                "affinity": affinity,
                "download_url": result_path,
                "protein_path": protein_pdb_path,  # Отдаем PDB для отрисовки
            }
        else:
            return {"status": "error", "message": "Vina не вернула энергию."}

    except Exception as e:
        print(f"🔴 ОШИБКА: {e}")
        return {"status": "error", "message": str(e)}
