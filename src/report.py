"""
report.py
Gera relatório em JSON + Markdown+PNG (gráficos) com resultados.
"""

import json
import os
import matplotlib.pyplot as plt
import pandas as pd

def generate_report_json(out_path, summary, per_track, concentration_est, params):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "tracks": per_track, "concentration": concentration_est, "params": params}, f, indent=2, ensure_ascii=False)
    return out_path

def generate_markdown_report(md_path, summary, per_track_df, concentration_est, params, plots=[]):
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Relatório automático - Análise de espermatozoides\n\n")
        f.write("## Parâmetros\n")
        for k,v in params.items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Resumo\n")
        for k,v in summary.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n## Concentração estimada\n")
        f.write(f"- {concentration_est:.2e} sptz/mL\n\n")
        if not per_track_df.empty:
            f.write("## Estatísticas por track (amostra)\n\n")
            f.write(per_track_df.head(50).to_markdown(index=False))
            f.write("\n\n")
        if plots:
            f.write("## Gráficos\n")
            for p in plots:
                f.write(f"![{os.path.basename(p)}]({os.path.basename(p)})\n")
    return md_path

def plot_velocity_histogram(velocities, out_png):
    plt.figure(figsize=(6,4))
    plt.hist(velocities, bins=30, color='C0', alpha=0.8)
    plt.xlabel("Velocidade (µm/s)")
    plt.ylabel("Número de trajetórias")
    plt.title("Histograma de velocidades")
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()
    return out_png