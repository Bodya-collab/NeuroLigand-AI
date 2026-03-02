from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import os
import uuid
from app.services.molecule_prep import convert_smiles_to_pdbqt
from app.services.docking import run_docking
from app.database import get_db
from app import models
from app.services.toxicity_predictor import analyze_lipinski

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
    print(f" [1/6] Request: {smiles}")
    job_id = str(uuid.uuid4())[:8]

    # Filesystem paths
    protein_pdb_path = f"data/uploaded/{job_id}_{protein_file.filename}"
    protein_pdbqt_path = f"data/temp/{job_id}_protein.pdbqt"

    # 1. Physical file handling
    content = await protein_file.read()
    lines = content.decode("utf-8").splitlines()

    with open(protein_pdb_path, "w", encoding="utf-8") as f_pdb, open(
        protein_pdbqt_path, "w", encoding="utf-8"
    ) as f_pdbqt:
        for line in lines:
            if line.startswith("ATOM"):
                # Save original PDB for visualization
                f_pdb.write(line + "\n")

                # PDBQT
                base = line[:54] 
                atom_name = line[12:16].strip()
                res_name = line[17:20].strip()

                # AutoDock Atom Type Assignment
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

                # Basis(54) + Occupancy(6) + TempFactor(6) + Padding(4) + Charge(6) + Padding(1) + Type(2)
                pdbqt_line = f"{base:<54}  1.00  0.00     0.000 {ad_type:<2}\n"
                f_pdbqt.write(pdbqt_line)

    print(f" [2/6] Converted to PDBQT")

    # AI-Radar for Pocket Detection
    if center_x == 0.0 and center_y == 0.0 and center_z == 0.0:
        from app.services.pocket_AI import get_smart_pocket

        center_x, center_y, center_z = get_smart_pocket(protein_pdb_path)
    # 2. Df
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
        # 3. Preparing ligand
        print(" [3/6] generating 3D ligand...")
        ligand_path = f"data/temp/{job_id}_ligand.pdbqt"
        convert_smiles_to_pdbqt(smiles, ligand_path)
        print(" [4/6] Starting VinaAuto...")

        # 4. Starting VinaAuto
        result_path = run_docking(
            protein_pdbqt_path, ligand_path, center_x, center_y, center_z
        )
        if not result_path:
            return {"status": "error", "message": "Ошибка Vina"}
            # 4. Start docking
        result_path = run_docking(
            protein_pdbqt_path, ligand_path, center_x, center_y, center_z
        )

        # Debug
        with open(result_path, "r") as f:
            print(f"СЫРОЙ ОТВЕТ VINA:\n{f.read()[:500]}")

        # Scanning interactions 
        from app.services.interactions import calculate_h_bonds

        h_bonds = calculate_h_bonds(protein_pdb_path, result_path)
        # -----------------------------------
        # 5. Parsing Vina result
        affinity = 0.0
        with open(result_path, "r") as f:
            for line in f:
                if line.startswith("REMARK VINA RESULT:"):
                    parts = line.split()
                    affinity = float(parts[3])
                    break
        # 5. Parsing Vina result
        affinity = 0.0
        with open(result_path, "r") as f:
            for line in f:
                if line.startswith("REMARK VINA RESULT:"):
                    # Pipe-separated values: "REMARK VINA RESULT: -7.5 0.0 0.0"
                    affinity = float(line.split()[3])
                    break

        # Adding "h_bonds" 
        # Lipinski analysis
        lipinski_data = analyze_lipinski(smiles)

        return {
            "status": "success",
            "affinity": affinity,
            "download_url": result_path,
            "protein_path": protein_pdb_path,
            "h_bonds": h_bonds,
            "lipinski": lipinski_data,
        }
        return {
            "status": "success",
            "affinity": affinity,
            "download_url": result_path,
            "protein_path": protein_pdb_path,
            "h_bonds": h_bonds,
        }

        if affinity is not None:
            new_job.status = "completed"
            new_job.result_affinity = affinity
            db.commit()
            return {
                "status": "success",
                "message": "Docking Completed Successfully!",
                "affinity": affinity,
                "download_url": result_path,
                "protein_path": protein_pdb_path, 
            }
        else:
            return {"status": "error", "message": "Vina не вернула энергию."}

    except Exception as e:
        print(f"🔴 ОШИБКА: {e}")
        return {"status": "error", "message": str(e)}
    # AI-generator


# If Depends not imported, add this at the top:
# from fastapi import Depends
from fastapi import BackgroundTasks, Form, File, UploadFile, Depends
from app.services.ai_generator import optimize_lead


@router.post("/dock-ai-candidate")
async def dock_ai_candidate(
    protein_file: UploadFile = File(...),
    original_smiles: str = Form(...),
    center_x: float = Form(0.0),
    center_y: float = Form(0.0),
    center_z: float = Form(0.0),
    db=Depends(get_db),  # FASTAPI df fot database session
):
    # 1. AI generating a better candidate
    ai_smiles = optimize_lead(original_smiles)
    if not ai_smiles:
        return {
            "status": "error",
            "message": "ИИ не смог сгенерировать стабильный аналог.",
        }

    # 2. End-to-end docking with the new AI-generated molecule
    result = await dock_molecule(
        protein_file=protein_file,
        smiles=ai_smiles,
        center_x=center_x,
        center_y=center_y,
        center_z=center_z,
        db=db,
    )

    # 3. Saving AI candidate to database
    result["ai_smiles"] = ai_smiles
    return result
