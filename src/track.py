"""
track.py
Rastreamento com DeepSORT usando as detecções do detect.py
Entrada: lista de detecções [frame_id, x1, y1, x2, y2, score]
Saída: dict tracks: {track_id: [(frame_id, cx, cy), ...]}
"""

from deep_sort_realtime.deepsort_tracker import DeepSort

class SpermTracker:
    def __init__(self, max_age=30, n_init=1):
        self.tracker = DeepSort(max_age=max_age, n_init=n_init)

    def run(self, detections, video_shape=None):
        """
        detections: list of [frame_id, x1, y1, x2, y2, score]
        retorna: dict {track_id: [(frame_id, cx, cy), ...]}
        """
        tracks = {}
        current_frame = -1
        batch = []
        for det in detections:
            frame_id, x1, y1, x2, y2, score = det
            if frame_id != current_frame and current_frame != -1:
                track_results = self._update_tracker(batch)
                for tr in track_results:
                    tid, ltrb, frame_index = tr
                    x1t, y1t, x2t, y2t = ltrb
                    cx = float((x1t + x2t) / 2.0)
                    cy = float((y1t + y2t) / 2.0)
                    tracks.setdefault(tid, []).append((frame_index, cx, cy))
                batch = []

            current_frame = frame_id
            w = x2 - x1
            h = y2 - y1
            batch.append(([float(x1), float(y1), float(w), float(h)], float(score), None, int(frame_id)))

        if batch:
            track_results = self._update_tracker(batch)
            for tr in track_results:
                tid, ltrb, frame_index = tr
                x1t, y1t, x2t, y2t = ltrb
                cx = float((x1t + x2t) / 2.0)
                cy = float((y1t + y2t) / 2.0)
                tracks.setdefault(tid, []).append((frame_index, cx, cy))

        return tracks

    def _update_tracker(self, batch):
        dets = []
        frame_index = None
        for item in batch:
            bbox, score, cls, fi = item
            dets.append((bbox, score, cls))
            frame_index = fi
        tracks = self.tracker.update_tracks(dets, frame=None)
        out = []
        for t in tracks:
            if not t.is_confirmed():
                continue
            track_id = t.track_id
            ltrb = t.to_ltrb()  # left top right bottom
            out.append((track_id, ltrb, frame_index))
        return out