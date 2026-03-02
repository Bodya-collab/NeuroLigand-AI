import streamlit as st
import requests
import os
from stmol import showmol
import py3Dmol
from rdkit import Chem
from rdkit.Chem import Draw

# Settings
st.set_page_config(page_title="NeuroLigand AI", page_icon="🧬", layout="wide")
API_URL = "http://127.0.0.1:8000/api/v1/dock-molecule"

# --- STREAMLIT ---
if "docking_result" not in st.session_state:
    st.session_state.docking_result = None

# --- CSS ---
st.markdown(
    """
    <style>
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; height: 3em; font-weight: bold; }
    .metric-card { background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #4e4e4e; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- Main Interface ---
st.title("🧪 NeuroLigand AI")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Parametrs")
    protein_file = st.file_uploader("Upload Protein (.pdb)", type=["pdb"])

    # Only input SMILES if protein is uploaded, otherwise show a warning
    smiles_input = st.text_input(
        "Drug Formula (SMILES)", value="CC(=O)Oc1ccccc1C(=O)O"
    )

    st.markdown("---")
    st.markdown("**Screening**")
    coord_cols = st.columns(3)
    with coord_cols[0]:
        center_x = st.number_input("Center X", value=0.0, format="%.3f")
    with coord_cols[1]:
        center_y = st.number_input("Center Y", value=0.0, format="%.3f")
    with coord_cols[2]:
        center_z = st.number_input("Center Z", value=0.0, format="%.3f")

    start_btn = st.button("Start calculation", type="primary")

with col2:
    st.subheader("Results")
    spin_model = st.checkbox("Spin the model ", value=True)

    if start_btn:
        if protein_file and smiles_input:
            with st.spinner("Calculating..."):
                try:
                    files = {
                        "protein_file": (protein_file.name, protein_file.getvalue())
                    }
                    data = {
                        "smiles": smiles_input,
                        "center_x": center_x,
                        "center_y": center_y,
                        "center_z": center_z,
                    }
                    response = requests.post(API_URL, files=files, data=data)
                    st.session_state.docking_result = response.json()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.docking_result:
        result = st.session_state.docking_result
        # Lipinski block 
        if "lipinski" in result and "error" not in result["lipinski"]:
            lip = result["lipinski"]
            st.markdown("### 💊 Bioavailability")

            # Green if good, red if bad
            c_mw = "#4CAF50" if lip["mw"] <= 500 else "#FF5722"
            c_logp = "#4CAF50" if lip["logp"] <= 5 else "#FF5722"
            c_hbd = "#4CAF50" if lip["hbd"] <= 5 else "#FF5722"
            c_hba = "#4CAF50" if lip["hba"] <= 10 else "#FF5722"

            cols = st.columns(4)
            cols[0].markdown(
                f"<div class='metric-card' style='padding: 10px;'><b>Weight (Da)</b><br><span style='color:{c_mw}; font-size:1.5em;'>{lip['mw']}</span></div>",
                unsafe_allow_html=True,
            )
            cols[1].markdown(
                f"<div class='metric-card' style='padding: 10px;'><b>LogP</b><br><span style='color:{c_logp}; font-size:1.5em;'>{lip['logp']}</span></div>",
                unsafe_allow_html=True,
            )
            cols[2].markdown(
                f"<div class='metric-card' style='padding: 10px;'><b>H-Donors</b><br><span style='color:{c_hbd}; font-size:1.5em;'>{lip['hbd']}</span></div>",
                unsafe_allow_html=True,
            )
            cols[3].markdown(
                f"<div class='metric-card' style='padding: 10px;'><b>H-Acceptors</b><br><span style='color:{c_hba}; font-size:1.5em;'>{lip['hba']}</span></div>",
                unsafe_allow_html=True,
            )

            if lip["is_druglike"]:
                st.success(
                    f"✅ Molecule is good as a drug! Violation: {lip['violations']}/4"
                )
            else:
                st.error(
                    f"⚠️ High risk of toxicity / poor absorption! Violations: {lip['violations']}/4"
                )

            st.markdown("---")

        if result.get("status") == "success" and "affinity" in result:
            affinity = result["affinity"]
            color = "#4CAF50" if affinity < -5 else "#FF5722"
            st.markdown(
                f"""
                <div class="metric-card">
                    <h2 style='margin:0; color:{color}'>Bond's energy</h2>
                    <h1 style='margin:0; font-size: 3em'>{affinity} <span style='font-size:0.5em'>kcal/mol</span></h1>
                </div>
            """,
                unsafe_allow_html=True,
            )

            docked_path = result.get("download_url")
            protein_path = result.get("protein_path")

            if docked_path and os.path.exists(docked_path):
                with open(docked_path, "r") as f:
                    raw_ligand = f.read()

                clean_ligand = ""
                for line in raw_ligand.split("\n"):
                    if line.startswith("MODEL 2"):
                        break
                    if not any(
                        tag in line
                        for tag in ["ROOT", "ENDROOT", "BRANCH", "ENDBRANCH", "TORSDOF"]
                    ):
                        clean_ligand += line + "\n"

                protein_data = ""
                if protein_path and os.path.exists(protein_path):
                    with open(protein_path, "r") as f:
                        protein_data = f.read()

                view = py3Dmol.view(width=800, height=500)

                if protein_data:
                    view.addModel(protein_data, "pdb")
                    view.setStyle(
                        {"model": 0}, {"cartoon": {"color": "#a0a0a0", "opacity": 0.8}}
                    )

                view.addModel(clean_ligand, "pdbqt")
                view.setStyle(
                    {"model": 1},
                    {"stick": {"colorscheme": "greenCarbon", "radius": 0.2}},
                )

                # --- 3. Draw interactions ---
                if "h_bonds" in result and len(result["h_bonds"]) > 0:
                    for bond in result["h_bonds"]:
                        # 1. Draw cyan sticks exactly on the ligand and protein atoms involved in the bond
                        view.addStyle(
                            {
                                "model": 0,
                                "resi": str(bond["start"]["res_num"]),
                                "chain": bond["start"]["chain"],
                            },
                            {"stick": {"colorscheme": "cyanCarbon", "radius": 0.15}},
                        )

                        # 2. Draw a dashed yellow cylinder between the two atoms to highlight the bond
                        view.addCylinder(
                            {
                                "start": dict(
                                    x=bond["start"]["x"],
                                    y=bond["start"]["y"],
                                    z=bond["start"]["z"],
                                ),
                                "end": dict(
                                    x=bond["end"]["x"],
                                    y=bond["end"]["y"],
                                    z=bond["end"]["z"],
                                ),
                                "radius": 0.1,
                                "color": "yellow",
                                "dashed": True,
                            }
                        )

                view.zoomTo()
                view.spin(spin_model)
                showmol(view, height=500, width=800)

                # Text info about interactions
                if "h_bonds" in result and len(result["h_bonds"]) > 0:
                    st.markdown("###  Details of interactions")
                    for bond in result["h_bonds"]:
                        st.markdown(
                            f"**Hydrogen bond:** `{bond['label']}` ⟷ `Ligand` | Distance: **{bond['distance']} Å**"
                        )
                elif "h_bonds" in result:
                    st.info("H-bonds were analyzed, but none were found in this complex.")
        else:
            st.error(f"Error: {result.get('message')}")
        # ==========================================================
        # AI-OPTIMIZATION BLOCK
        # ==========================================================
        st.markdown("---")
        st.subheader("🤖 AI-optimalization (Hit-to-Lead)")
        st.info(
            "AI generates 40 optimized analogs of the original molecule and pick the best one."
        )

        if st.button("Find the best candidate", type="primary"):
            with st.spinner(
                " AI generates candidates and runs quantum calculation..."
            ):
                try:
                    files = {
                        "protein_file": (protein_file.name, protein_file.getvalue())
                    }
                    data = {
                        "original_smiles": smiles_input,
                        "center_x": center_x,
                        "center_y": center_y,
                        "center_z": center_z,
                    }
                    # Endpdoint for AI optimization 
                    ai_response = requests.post(
                        "http://127.0.0.1:8000/api/v1/dock-ai-candidate",
                        files=files,
                        data=data,
                    )
                    st.session_state.ai_docking_result = ai_response.json()
                except Exception as e:
                    st.error(f"Error connecting to AI: {e}")

        # --- ОТРИСОВКА РЕЗУЛЬТАТА ИИ ---
        if st.session_state.get("ai_docking_result"):
            ai_res = st.session_state.ai_docking_result

            if ai_res.get("status") == "success":
                st.success(f"**Generated AI Candidate:** `{ai_res['ai_smiles']}`")

                # ==========================================
                # Draing the chemical structure of the AI candidate
                # ==========================================
                mol = Chem.MolFromSmiles(ai_res["ai_smiles"])
                if mol:
                    # Generating the image of the molecule
                    img = Draw.MolToImage(mol, size=(400, 250))
                    # Centering
                    col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
                    with col_img2:
                        st.image(
                            img,
                            caption="Chemical structure of the AI candidate",
                            use_container_width=True,
                        )
                # ==========================================

                # Ai card with affinity and download button
                ai_affinity = ai_res["affinity"]
                color = (
                    "#4CAF50" if ai_affinity < affinity else "#FF5722"
                )
                st.markdown(
                    f"""
                    <div class="metric-card" style="border: 2px solid {color};">
                        <h2 style='margin:0; color:{color}'>AI Candidate Energy</h2>
                        <h1 style='margin:0; font-size: 3em'>{ai_affinity} <span style='font-size:0.5em'>kcal/mol</span></h1>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                # Download button for the AI-docked molecule
                with open(ai_res["download_url"], "rb") as file:
                    st.download_button(
                        label="📥 Download AI Candidate PDBQT",
                        data=file,
                        file_name="AI_candidate_docked.pdbqt",
                        mime="chemical/x-pdb",
                    )
            else:
                st.error(f"Error with AI: {ai_res.get('message')}")
