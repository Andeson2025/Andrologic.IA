"""
vigor.py
Índice de vigor simples: vigor = velocity * linearity
Classificação: Alto / Médio / Baixo
"""

def vigor_index(vel_um_s, lin):
    return vel_um_s * lin

def vigor_class(v):
    if v > 15:
        return "Alto"
    elif v > 5:
        return "Médio"
    else:
        return "Baixo"