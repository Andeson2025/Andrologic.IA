"""
motility.py
Cálculos de distância, velocidade, retilinearidade (linearity)
Assume trajetórias como listas: [(frame_id, x, y), ...]
"""

import numpy as np

def distance_pixels(traj):
    """Distância total percorrida em pixels"""
    if len(traj) < 2:
        return 0.0
    dist = 0.0
    for i in range(1, len(traj)):
        x1, y1 = traj[i-1][1], traj[i-1][2]
        x2, y2 = traj[i][1], traj[i][2]
        dist += np.hypot(x2 - x1, y2 - y1)
    return float(dist)

def velocity_um_s(traj, fps, microns_per_pixel):
    """Velocidade média (µm/s) ao longo da trajetória"""
    if len(traj) < 2:
        return 0.0
    dist_px = distance_pixels(traj)
    total_seconds = (traj[-1][0] - traj[0][0]) / float(fps) if fps > 0 else (len(traj)/fps if fps>0 else 1)
    if total_seconds <= 0:
        total_seconds = len(traj) / float(fps) if fps > 0 else 1.0
    dist_um = dist_px * microns_per_pixel
    return float(dist_um / total_seconds)

def linearity(traj):
    """Retilinearidade = distance straight line / total distance (0..1)"""
    if len(traj) < 2:
        return 0.0
    x0, y0 = traj[0][1], traj[0][2]
    xn, yn = traj[-1][1], traj[-1][2]
    straight = np.hypot(xn - x0, yn - y0)
    total = distance_pixels(traj)
    if total == 0:
        return 0.0
    return float(straight / total)