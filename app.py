"""
app.py
Flask backend que serve a página e executa a pipeline de análise quando um vídeo/imagem é enviado.
"""

import os
import uuid
import time
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.detect import SpermDetector
from src.track import SpermTracker
from src.motility import distance_pixels, velocity_um_s, linearity
from src.vigor import vigor_index, vigor_class
from src.concentration import estimate_concentration
from src.report import generate_report_json, generate_markdown_report, plot_velocity_histogram
from src.visualize import draw_tracks_on_video

import pandas as pd

UPLOAD_FOLDER = "uploads"
REPORTS_FOLDER = "reports"
ALLOWED_EXT = {"mp4", "mov", "avi", "mkv", "mpg", "mpeg", "jpg", "jpeg", "png"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)
os.makedirs("models/yolo", exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2GB

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reports/<path:filename>")
def reports_files(filename):
    return send_from_directory(app.config["REPORTS_FOLDER"], filename)

@app.route("/upload_example")
def upload_example():
    # Placeholder route if quiser servir um exemplo
    return jsonify({"ok": True})

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Recebe: file (vídeo/imagem), microns_per_pixel, fps, drop_volume_ul, conf
    Retorna: JSON com paths para report, markdown e vídeo processado
    """
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado (campo 'file')."}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Arquivo sem nome."}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "Extensão não permitida."}), 400

    # parâmetros
    microns_per_pixel = float(request.form.get("microns_per_pixel", 0.5))
    fps = float(request.form.get("fps", 25.0))
    drop_volume_ul = float(request.form.get("drop_volume_ul", 2.0))
    conf = float(request.form.get("conf", 0.25))
    weights = request.form.get("weights", "models/yolo/yolov8n.pt")
    max_frames = request.form.get("max_frames")
    max_frames = int(max_frames) if max_frames else None

    uid = str(int(time.time())) + "_" + uuid.uuid4().hex[:6]
    filename = secure_filename(f.filename)
    in_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{uid}_{filename}")
    f.save(in_path)

    # criar diretório do relatório
    out_base = os.path.join(app.config["REPORTS_FOLDER"], uid)
    os.makedirs(out_base, exist_ok=True)
    out_json_path = os.path.join(out_base, "report.json")
    out_md_path = os.path.join(out_base, "report.md")
    out_hist = os.path.join(out_base, "vel_hist.png")
    out_video = os.path.join(out_base, "processed.mp4")

    # Run pipeline (bloqueante) - para uso local é aceitável; para produção usar fila/worker
    try:
        detector = SpermDetector(weights=weights, conf=conf)
        detections = detector.detect_video(in_path, max_frames=max_frames)
        tracker = SpermTracker()
        tracks = tracker.run(detections)

        # Calcular métricas por track
        rows = []
        velocities = []
        counts_per_frame = {}
        for tid, traj in tracks.items():
            traj_sorted = sorted(traj, key=lambda x: x[0])
            dist_px = distance_pixels(traj_sorted)
            vel = velocity_um_s(traj_sorted, fps=fps, microns_per_pixel=microns_per_pixel)
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
            for fr, cx, cy in traj_sorted:
                counts_per_frame.setdefault(fr, set()).add(tid)

        counts_list = [len(s) for s in counts_per_frame.values()] if counts_per_frame else []
        conc = estimate_concentration(counts_list, drop_volume_ul)

        df = pd.DataFrame(rows)
        summary = {}
        if not df.empty:
            summary["motilidade_progressiva_%"] = float((df[(df.velocity_um_s > 25) & (df.linearity > 0.6)].shape[0] / df.shape[0]) * 100)
            summary["vigor_medio"] = float(df["vigor_index"].mean())
            summary["n_trajetorias"] = int(df.shape[0])
        else:
            summary["motilidade_progressiva_%"] = 0.0
            summary["vigor_medio"] = 0.0
            summary["n_trajetorias"] = 0

        params = {
            "weights": weights,
            "conf": conf,
            "microns_per_pixel": microns_per_pixel,
            "fps": fps,
            "drop_volume_ul": drop_volume_ul
        }

        # gerar outputs
        generate_report_json(out_json_path, summary, df.to_dict(orient="records"), conc, params)
        plots = []
        if velocities:
            plot_velocity_histogram(velocities, out_hist)
            plots.append(out_hist)

        # gerar markdown
        generate_markdown_report(out_md_path, summary, df, conc, params, plots=plots)

        # gerar vídeo processado com trilhas desenhadas
        draw_tracks_on_video(in_path, tracks, out_video)

        # responder com links relativos
        base_url = "/reports/" + uid + "/"
        response = {
            "status": "done",
            "report_json": base_url + "report.json",
            "report_md": base_url + "report.md",
            "histogram": base_url + os.path.basename(out_hist) if plots else None,
            "processed_video": base_url + os.path.basename(out_video),
            "summary": summary
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)