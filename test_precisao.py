#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from tri_enem import verificar_precisao_prova

# Testar import direto do pacote principal
r = verificar_precisao_prova(2009, 'LC', 57)
print(f"Status: {r.get('status')}")
print(f"Aviso: {r.get('aviso')}")
print(f"MAE: {r.get('mae')}")
print("OK - Import funcionando!")
