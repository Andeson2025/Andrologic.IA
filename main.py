"""
main.py
Pipeline everything-in-one:
1) Detect via YOLOv8
2) Track via DeepSORT
3) Calcular motilidade, vigor
4) Estimar concentração
5) Gerar relatório (JSON + Markdown + PNG)
Uso:
python main.py --input data/raw_videos/sample.mp4 --output reports/sample_report.json --microns_per_pixel 0.5 --fps 25 --drop_volume_ul 2.0
"""

import argparse
import os
from src.detect import SpermDetector
from src.track import SpermTracker
from src.motility import distance_pixels, velocity_um_s, linearity
from src.vigor import vigor_index, vigor_class
from src.concentration import estimate_concentration
from src.report import generate_report_json, generate_markdown_report, plot_velocity_histogram
import pandas as pd
from tqdm import tqdm

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Vídeo de entrada")
    p.add_argument("--output", required=True, help="Arquivo JSON de saída do relatório")
    p.add_argument("--weights", default="models/yolo/yolov8n.pt", help="Pesos YOLOv8")
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--microns_per_pixel", type=float, default=0.5)
    p.add_argument("--fps", type=float, default=25.0)
    p.add_argument("--drop_volume_ul", type=float, default=2.0, help="Volume da gota correspondente ao campo em µL")
    p.add_argument("--max_frames", type=int, default=None)
    return p.parse_args()

def main():
    args = parse_args()
    detector = SpermDetector(weights=args.weights, conf=args.conf)
    print("Detectando...")
    detections = detector.detect_video(args.input, max_frames=args.max_frames)
    print(f"Detecções totais: {len(detections)}")

    tracker = SpermTracker()
    print("Rastreando...")
    tracks = tracker.run(detections)

    # Calcular por track
    rows = []
    velocities = []
    counts_per_frame = {}
    for tid, traj in tracks.items():
        # traj é [(frame_id, cx, cy), ...] ; ordenar por frame
        traj_sorted = sorted(traj, key=lambda x: x[0])
        dist_px = distance_pixels(traj_sorted)
        vel = velocity_um_s(traj_sorted, fps=args.fps, microns_per_pixel=args.microns_per_pixel)
        lin = linearity(traj_sorted)
        vigor_idx = vigor_index(vel, lin)
        vclass = vigor_class(vigor_idx)
        rows.append({
            "track_id": int(tid),
            "n_points": len(traj_sorted),
            "distance_px": dist_px,
            "velocity_um_s": vel,
            "linearity": lin,
            "vigor_index": vigor_idx,
            "vigor_class": vclass
        })
        velocities.append(vel)
        # contar por frame para concentração
        for fr, cx, cy in traj_sorted:
            counts_per_frame.setdefault(fr, set()).add(tid)

    counts_list = [len(s) for s in counts_per_frame.values()] if counts_per_frame else []
    conc = estimate_concentration(counts_list, args.drop_volume_ul)

    df = pd.DataFrame(rows)
    summary = {}
    if not df.empty:
        summary["motilidade_progressiva_%"] = float((df[(df.velocity_um_s > 25) & (df.linearity > 0.6)].shape[0] / df.shape[0]) * 100)
        summary["vigor_medio"] = df["vigor_index"].mean()
        summary["n_trajetorias"] = int(df.shape[0])
    else:
        summary["motilidade_progressiva_%"] = 0.0
        summary["vigor_medio"] = 0.0
        summary["n_trajetorias"] = 0

    params = {
        "weights": args.weights,
        "conf": args.conf,
        "microns_per_pixel": args.microns_per_pixel,
        "fps": args.fps,
        "drop_volume_ul": args.drop_volume_ul
    }

    # gerar outputs
    out_json = generate_report_json(args.output, summary, df.to_dict(orient="records"), conc, params)
    # gerar markdown ao lado do json
    md_path = os.path.splitext(args.output)[0] + ".md"
    plots = []
    if velocities:
        hist_png = os.path.splitext(args.output)[0] + "_vel_hist.png"
        plot_velocity_histogram(velocities, hist_png)
        plots.append(hist_png)
    generate_markdown_report(md_path, summary, df, conc, params, plots=plots)

    print("Relatório gerado:")
    print(out_json)
    print(md_path)

if __name__ == "__main__":
    main()