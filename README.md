# NeuroLigand AI 🧬

> **A comprehensive web platform for Structure-Based Drug Design (SBDD) and AI-driven Hit-to-Lead optimization.**

NeuroLigand AI is an end-to-end bioinformatics tool designed for medicinal chemists and computational biologists. The system seamlessly integrates molecular docking, pharmacokinetic screening, and generative Deep Learning to automatically discover, evaluate, and visualize novel drug candidates directly in the browser.

---

## 📸 Platform Overview

<p align="center">
  <img width="897" height="619" alt="image" src="https://github.com/user-attachments/assets/13db5df5-4f64-473a-be97-4d4fc9f22612" />
  <br>
  <em>Main interface: Target protein upload, baseline ligand SMILES input, and optional targeted docking grid setup.</em>
</p>

---

## ✨ Key Features

* **Molecular Docking Engine:** Perform both blind and targeted molecular docking using **AutoDock Vina**.
* **AI Hit-to-Lead Optimization:** Generate novel structural analogs of known drugs using a generative Transformer model (**ChemGPT**).
* **Pharmacokinetic Screening:** Automatically filter out potentially toxic or non-absorbable compounds prior to heavy computations using **Lipinski's Rule of Five** (via RDKit).
* **Advanced 3D Visualization:** Interactive rendering of protein-ligand complexes with automated hydrogen bond detection and distance calculations (precision up to 0.01 Å).
* **2D Cheminformatics:** Instant 2D structure generation for AI-proposed molecular candidates.

## 🏆 Proof of Work & Validation

We don't just calculate; we validate and visualize. The NeuroLigand AI pipeline is tested against experimental data and provides deep, precise insights into molecular interactions.

### 🔬 Experimental vs. Computational (Sildenafil)
For **Sildenafil** binding to **PDE5** (PDB: **1TBF**), our pipeline accurately predicted the binding mode, achieving a binding affinity of **-4.806 kcal/mol**, which strongly aligns with the experimental value derived from Ki (-7,44 kcal/mol).

<p align="center">
  <img width="1784" height="838" alt="image" src="https://github.com/user-attachments/assets/48963c16-5c6f-47e5-884f-1b7ace35507d" />
  <br>
  <em>Visualization of docking results: Automated 3D rendering of the complex with hydrogen bonds (yellow dotted lines) and Lipinski’s R5 safety panel.</em>
</p>

### 🤖 AI-Driven Optimization
The integrated **ChemGPT Transformer** model can take a baseline drug like Aspirin and generate structural analogs. In the example below, the AI suggested adding a methyl ester group, and our automated pipeline immediately performed docking and 2D visualization for the new candidate.

<p align="center">
 <img width="1252" height="746" alt="image" src="https://github.com/user-attachments/assets/d184099f-a210-4bfe-9d65-6c2c3e04ad4f" />
  <br>
  <em>Generative optimization loop: The AI suggests a new structure, RDKit renders the 2D molecule, and AutoDock Vina calculates the new binding affinity for instant comparison.</em>
</p>

## 🛠 Tech Stack

* **Frontend:** Streamlit
* **Backend:** FastAPI, Python 3.10+
* **Cheminformatics:** RDKit
* **Docking:** AutoDock Vina, OpenBabel
* **Machine Learning:** PyTorch, Hugging Face `transformers`
* **3D Rendering:** `py3Dmol`

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/NeuroLigand-AI.git](https://github.com/your-username/NeuroLigand-AI.git)
   cd NeuroLigand-AI
