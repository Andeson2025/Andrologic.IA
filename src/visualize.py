"""
visualize.py
Desenha trilhas no vídeo original e salva um vídeo processado.
Entrada:
- video_path: caminho do vídeo original
- tracks: dict {track_id: [(frame_id, cx, cy), ...]}
- out_path: caminho para salvar o vídeo com sobreposição
"""

import cv2
import os
import random

def _color_for_id(i):
    random.seed(i)
    return (random.randint(50,255), random.randint(50,255), random.randint(50,255))

def draw_tracks_on_video(video_path, tracks, out_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível abrir o vídeo para visualização.")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    # construir mapa frame -> list of (track_id, cx, cy)
    frame_map = {}
    for tid, traj in tracks.items():
        for fr, cx, cy in traj:
            frame_map.setdefault(fr, []).append((tid, int(cx), int(cy)))

    frame_id = 0
    # para desenhar rastro acumulado, guardamos últimas posições por track
    trails = {tid: [] for tid in tracks.keys()}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_id in frame_map:
            for tid, cx, cy in frame_map[frame_id]:
                trails[tid].append((cx, cy))
        # desenhar trilhas
        for tid, points in trails.items():
            color = _color_for_id(tid)
            # desenhar linhas do rastro
            for i in range(1, len(points)):
                cv2.line(frame, points[i-1], points[i], color, 2)
            # desenhar último ponto
            if points:
                cv2.circle(frame, points[-1], 4, color, -1)
                cv2.putText(frame, f"ID:{tid}", (points[-1][0]+5, points[-1][1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        out.write(frame)
        frame_id += 1

    cap.release()
    out.release()
    return out_path