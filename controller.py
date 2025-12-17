import csv
import sqlite3
import cantools
from cantools.database.can.signal import NamedSignalValue
import numpy as np


class Controller:
    def __init__(self):
        self.conn = sqlite3.connect('telem.db')
        self.cur = self.conn.cursor()

        self.tables = set()
        self.numerical = {}

    def load_log(self, file):
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for (table,) in self.cur.fetchall():
            self.cur.execute(f'DROP TABLE IF EXISTS "{table}"')
        self.conn.commit()

        self.tables.clear()
        self.numerical.clear()

        frucd_db = cantools.database.load_file('20240129 Gen5 CAN DB.dbc')
        mc_db = cantools.database.load_file('FE12.dbc')

        with open(file, 'r', newline='') as raw:
            reader = csv.reader(raw)
            for row in reader:
                if not row or len(row) < 10:
                    continue

                try:
                    frame_id = int(row[0], 16)
                except Exception:
                    continue

                message = None
                for db in (frucd_db, mc_db):
                    try:
                        message = db.get_message_by_frame_id(frame_id)
                        break
                    except KeyError:
                        pass

                if message is None:
                    continue

                try:
                    data = [int(b) if b else 0 for b in row[1:9]]
                    timestamp = int(row[-1])
                except Exception:
                    continue

                try:
                    decoded = message.decode(bytes(data))
                except Exception:
                    continue

                src = message.senders[0] if getattr(message, "senders", None) and len(message.senders) else "Unknown"

                if message.name not in self.tables:
                    cols = ['"Timestamp" INTEGER', '"Source" TEXT']
                    for sig in message.signals:
                        v = decoded.get(sig.name, None)
                        t = 'REAL' if isinstance(v, (float, int, np.integer, np.floating)) else 'TEXT'
                        cols.append(f'"{sig.name}" {t}')

                    self.cur.execute(
                        f'CREATE TABLE "{message.name}" ({", ".join(cols)})'
                    )
                    self.tables.add(message.name)

                columns = ['"Timestamp"', '"Source"']
                values = [timestamp, src]

                for sig in message.signals:
                    v = decoded.get(sig.name, None)
                    if isinstance(v, NamedSignalValue):
                        v = str(v)

                    columns.append(f'"{sig.name}"')
                    values.append(v)

                    if isinstance(v, (float, int, np.integer, np.floating)):
                        self.numerical.setdefault(src, {}) \
                            .setdefault(message.name, set()) \
                            .add(sig.name)

                q = f'''
                    INSERT INTO "{message.name}"
                    ({", ".join(columns)})
                    VALUES ({",".join("?" * len(values))})
                '''
                self.cur.execute(q, values)

        self.conn.commit()

    def _fetch_signal(self, msg, sig):
        self.cur.execute(
            f'SELECT Timestamp, "{sig}" FROM "{msg}" ORDER BY Timestamp'
        )
        rows = self.cur.fetchall()
        if not rows:
            return np.array([], dtype=float), np.array([], dtype=float)

        t = np.array([r[0] for r in rows], dtype=float) / 1000.0
        y = np.array([r[1] for r in rows])

        # force numeric where possible
        try:
            y = y.astype(float)
        except Exception:
            y = np.array([float(v) if v is not None else np.nan for v in y], dtype=float)

        return t, y

    def get_datasets(self, selected):
        datasets = []

        for src, msgs in (selected or {}).items():
            for msg, sigs in msgs.items():
                for sig in sigs:
                    t, y = self._fetch_signal(msg, sig)
                    datasets.append((sig, t, y, "ts"))

        return datasets

    def _zoh_resample(self, t_src, y_src, t_new):
        t_src = np.asarray(t_src, dtype=float)
        y_src = np.asarray(y_src, dtype=float)
        t_new = np.asarray(t_new, dtype=float)

        if t_src.size == 0 or y_src.size == 0:
            return np.full(t_new.shape, np.nan, dtype=float)

        order = np.argsort(t_src)
        t_src = t_src[order]
        y_src = y_src[order]

        idx = np.searchsorted(t_src, t_new, side="right") - 1
        out = np.full(t_new.shape, np.nan, dtype=float)

        valid = idx >= 0
        out[valid] = y_src[idx[valid]]
        return out

    def get_xy_dataset(self, x_sel, y_sel, dt=0.02):
        if not x_sel or not y_sel:
            return None

        # selections are tuples: (src, msg, sig)
        _, x_msg, x_sig = x_sel
        _, y_msg, y_sig = y_sel

        tx, x = self._fetch_signal(x_msg, x_sig)
        ty, y = self._fetch_signal(y_msg, y_sig)

        if tx.size == 0 or ty.size == 0:
            return None

        t_start = max(np.min(tx), np.min(ty))
        t_stop = min(np.max(tx), np.max(ty))
        if not np.isfinite(t_start) or not np.isfinite(t_stop) or t_stop <= t_start:
            return None

        dt = float(dt) if dt and float(dt) > 0 else 0.02
        t_new = np.arange(t_start, t_stop, dt, dtype=float)

        xz = self._zoh_resample(tx, x, t_new)
        yz = self._zoh_resample(ty, y, t_new)

        ok = np.isfinite(xz) & np.isfinite(yz)
        x_out = xz[ok]
        y_out = yz[ok]

        name = f"{y_sig} vs {x_sig}"
        return (name, x_out, y_out, "xy", x_sig, y_sig)

    def export_csv(self, file_a, file_b, out_path):
        def rows(fp):
            r = csv.reader(fp)
            for row in r:
                try:
                    yield int(row[-1]), row
                except:
                    pass

        with open(file_a) as fa, open(file_b) as fb, open(out_path, "w", newline="") as fo:
            wa, wb = rows(fa), rows(fb)
            writer = csv.writer(fo)

            a, b = next(wa, None), next(wb, None)

            while a and b:
                if a[0] <= b[0]:
                    writer.writerow(a[1])
                    a = next(wa, None)
                else:
                    writer.writerow(b[1])
                    b = next(wb, None)

            for rem in (wa, wb):
                for _, row in rem:
                    writer.writerow(row)

        print(f"Merged logs written to {out_path}")