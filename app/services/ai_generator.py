from transformers import pipeline
from rdkit import Chem
from rdkit.Chem import Descriptors
import re

print("Loading AI Generator model...")
generator = pipeline("text-generation", model="ncfrey/ChemGPT-4.7M")


def optimize_lead(original_smiles: str):
    print(f"working on: {original_smiles}")

    seed_text = original_smiles[:5]

    candidates = []
    try:
        # Giving attempts for AI  (30) (temp 1.0)
        results = generator(
            seed_text,
            max_length=60,
            num_return_sequences=30,
            do_sample=True,
            temperature=1.0,
            pad_token_id=50256,
        )

        for res in results:
            raw_text = res["generated_text"]
            clean = re.sub(r"\[[A-Za-z]{2,}[0-9]*\]", "", raw_text)
            clean = re.sub(r"[^A-Za-z0-9@+\-\[\]\(\)\\\/%=#]", "", clean)

            # Verifying RDKit
            if len(clean) > 5 and clean != original_smiles:
                mol = Chem.MolFromSmiles(clean)
                if mol is not None:
                    if Descriptors.MolWt(mol) < 550:
                        candidates.append(clean)

            if len(candidates) >= 5:  # If we got 5 good candidates, we can stop asking the AI for more
                break

        if candidates:
            # The best candidate is the longest valid SMILES (as a proxy for complexity)
            best_candidate = sorted(candidates, key=len, reverse=True)[0]
            print(f"✨ [ИИ] Успех! Выбран аналог: {best_candidate}")
            return best_candidate

        # If AI fails to generate anything valid, we can try a simple fallback: just add a methyl group to the original molecule
        # Adding a methyl group is a common medicinal chemistry trick to improve binding affinity and pharmacokinetics, and it's a simple way to get a "better" molecule if the AI fails.
        print("AI failed to generate a valid candidate. Trying a simple fallback...")
        fallback_smiles = original_smiles + "C"

        if Chem.MolFromSmiles(fallback_smiles):
            return fallback_smiles
        return None

    except Exception as e:
        print(f"Error {e}")
        return None

    # Picking the best candidate based on some heuristic (e.g., longest valid SMILES, or lowest predicted molecular weight)
    seed_length = max(4, len(original_smiles) // 2)
    seed_text = original_smiles[:seed_length]

    candidates = []
    try:
        # Generating a batch of candidates (20) with a higher temperature for more creativity
        results = generator(
            seed_text,
            max_length=50,
            num_return_sequences=20,
            do_sample=True,
            temperature=1.2,
            pad_token_id=50256,
        )

        for res in results:
            raw_text = res["generated_text"]
            # Cleaning
            clean = re.sub(r"\[[A-Za-z]{2,}[0-9]*\]", "", raw_text)
            clean = re.sub(r"[^A-Za-z0-9@+\-\[\]\(\)\\\/%=#]", "", clean)

            # Verifying with RDKit and basic filters
            if len(clean) > 5 and clean != original_smiles:
                mol = Chem.MolFromSmiles(clean)
                if mol is not None:
                    # Checking molecular weight 
                    if Descriptors.MolWt(mol) < 550:
                        candidates.append(clean)

            if len(candidates) >= 10: 
                break

        if not candidates:
            return None

        # The best candidate is the longest valid SMILES (as a proxy for complexity)
        best_candidate = sorted(candidates, key=len, reverse=True)[0]
        print(f"✨ [ИИ] Выбран лучший кандидат из 10: {best_candidate}")
        return best_candidate

    except Exception as e:
        print(f"Error {e}")
        return None
