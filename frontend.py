import streamlit as st
import requests
import os
from stmol import showmol
import py3Dmol

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="NeuroLigand AI", page_icon="🧬", layout="wide")
API_URL = "http://127.0.0.1:8000/api/v1/dock-molecule"

# --- CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; height: 3em; font-weight: bold; }
    .metric-card { background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #4e4e4e; }
    </style>
""", unsafe_allow_html=True)

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🧪 Виртуальная Лаборатория")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Параметры")
    protein_file = st.file_uploader("Загрузить Белок (.pdb)", type=["pdb"])
    smiles_input = st.text_input("Формула Лекарства (SMILES)", value="CC(=O)Oc1ccccc1C(=O)O")
    
    # НОВЫЙ БЛОК: Снайперский прицел
    st.markdown("---")
    st.markdown("**🎯 Снайперский прицел (Опционально)**")
    st.caption("Введите координаты кармана. Если оставить нули, система ударит в центр белка.")
    coord_cols = st.columns(3)
    with coord_cols[0]: center_x = st.number_input("Center X", value=0.0, format="%.3f")
    with coord_cols[1]: center_y = st.number_input("Center Y", value=0.0, format="%.3f")
    with coord_cols[2]: center_z = st.number_input("Center Z", value=0.0, format="%.3f")
    
    start_btn = st.button("🚀 ЗАПУСТИТЬ РАСЧЕТ")

with col2:
    st.subheader("2. Результат")
    if start_btn:
        if protein_file and smiles_input:
            with st.spinner("⏳ Идет расчет..."):
                try:
                    files = {"protein_file": (protein_file.name, protein_file.getvalue())}
                    
                    # НОВАЯ ОТПРАВКА ДАННЫХ (с координатами)
                    data = {
                        "smiles": smiles_input,
                        "center_x": center_x,
                        "center_y": center_y,
                        "center_z": center_z
                    }
                    response = requests.post(API_URL, files=files, data=data)
                    result = response.json()
                    
                    if result.get("status") == "success" and "affinity" in result:
                        affinity = result['affinity']
                        color = "#4CAF50" if affinity < -5 else "#FF5722"
                        st.markdown(f"""
                            <div class="metric-card">
                                <h2 style='margin:0; color:{color}'>Энергия связи</h2>
                                <h1 style='margin:0; font-size: 3em'>{affinity} <span style='font-size:0.5em'>kcal/mol</span></h1>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        docked_path = result.get('download_url')
                        protein_path = result.get('protein_path')
                        
                        if docked_path and os.path.exists(docked_path):
                            with open(docked_path, "r") as f:
                                raw_ligand = f.read()
                            
                            # --- ХАК: ЛЕЧИМ ОТОБРАЖЕНИЕ ХВОСТОВ ---
                            clean_ligand = ""
                            for line in raw_ligand.split('\n'):
                                if not any(tag in line for tag in ["ROOT", "ENDROOT", "BRANCH", "ENDBRANCH", "TORSDOF"]):
                                    clean_ligand += line + '\n'

                            protein_data = ""
                            if protein_path and os.path.exists(protein_path):
                                with open(protein_path, "r") as f: protein_data = f.read()

                            view = py3Dmol.view(width=800, height=500)
                            
                            if protein_data:
                                view.addModel(protein_data, "pdb")
                                view.setStyle({'model': -1}, {"cartoon": {'color': 'gray'}})
                            
                            view.addModel(clean_ligand, "pdbqt")
                            view.setStyle({'model': -1}, {"stick": {'colorscheme': 'greenCarbon', 'radius': 0.2}})
                            
                            view.zoomTo()
                            view.spin(True)
                            showmol(view, height=500, width=800)
                    else:
                        st.error(f"Ошибка: {result.get('message')}")
                except Exception as e:
                    st.error(f"Ошибка соединения: {e}")