import pandas as pd
import os
import json
import glob

def contar_participantes():
    base_dir = r"microdados_limpos"
    output_file = r"tri_enem/participantes_por_pr ova.json"
    
    resultados = {}
    
    # Iterate over years
    years = sorted([d for d in os.listdir(base_dir) if d.isdigit()])
    
    print(f"Found years: {years}")
    
    for year in years:
        year_path = os.path.join(base_dir, year, f"DADOS_ENEM_{year}.csv")
        if not os.path.exists(year_path):
            print(f"Skipping {year}: File not found")
            continue
            
        print(f"Processing {year}...")
        try:
            # We need CO_PROVA columns. separators vary? Check default (usually ; or ,)
            # Analise-enem usually uses ; for cleaned data?
            # Let's try ; first, as seen in investigate logs
            
            df = pd.read_csv(year_path, sep=';', usecols=lambda x: x.startswith('CO_PROVA_'))
            
            # Melt or stack to get all proofs in one series
            # Counts per proof code
            counts = df.stack().value_counts().to_dict()
            
            # Convert keys to int (if possible) and values to int
            clean_counts = {}
            for k, v in counts.items():
                try:
                    clean_counts[int(float(k))] = int(v)
                except ValueError:
                    continue # Skip non-numeric values if any
            
            resultados[year] = clean_counts
            print(f"  {year}: Found {len(clean_counts)} distinct proof codes.")
            
        except Exception as e:
            print(f"Error processing {year}: {e}")

    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(resultados, f, indent=2)
        
    print(f"Saved counts to {output_file}")

if __name__ == "__main__":
    contar_participantes()
