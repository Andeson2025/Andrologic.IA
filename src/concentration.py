"""
concentration.py
Estimativa simples de concentração:
- conta número médio de espermatozoides por campo (frame)
- usa volume da gota (uL) para converter para sptz/mL
"""

import numpy as np

def estimate_concentration(counts_per_frame, volume_ul):
    if len(counts_per_frame) == 0 or volume_ul <= 0:
        return 0.0
    mean_count = float(np.mean(counts_per_frame))
    conc_per_ml = (mean_count / volume_ul) * 1000.0
    return float(conc_per_ml)