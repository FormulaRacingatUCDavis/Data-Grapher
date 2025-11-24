import csv
import sqlite3
import cantools
from cantools.database.can.signal import NamedSignalValue
import numpy

class Controller(object):
    def __init__(self):
        self.conn = sqlite3.connect('telem.db')
        self.cur = self.conn.cursor()

        self.tables = set()
        self.numerical = {} # {src: {message: signal}}

    def load_log(self, file):
        """
        Process log file data into SQLite database with proper column types.
        """
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for (table,) in self.cur.fetchall():
            self.cur.execute(f'DROP TABLE IF EXISTS "{table}"')
        self.conn.commit()
        self.tables.clear()
        self.numerical.clear()

        failed = set()
        count = 0

        frucd_db = cantools.database.load_file('20240129 Gen5 CAN DB.dbc')
        mc_db = cantools.database.load_file('FE12.dbc')

        with open(file, 'r', newline='') as raw_can:
            reader = csv.reader(raw_can)
            for row in reader:
                frame_id = int(row[0], 16)

                message = None
                for db in (frucd_db, mc_db):
                    try:
                        message = db.get_message_by_frame_id(frame_id)
                        break
                    except KeyError:
                        continue

                if message is None:
                    failed.add(frame_id)
                    count += 1
                    continue

                data_bytes = []
                for b in row[1:9]:
                    if b.strip() == '':
                        data_bytes.append(0)
                    else:
                        try:
                            data_bytes.append(int(b))
                        except ValueError:
                            data_bytes.append(0)

                timestamp = int(row[-1])
                decoded = message.decode(bytes(data_bytes))
                src = message.senders[0]

                if message.name not in self.tables:
                    col_defs = [
                        '"Timestamp" INTEGER',
                        '"Source" TEXT'
                    ]

                    for sig in message.signals:
                        test_value = decoded[sig.name]

                        if isinstance(test_value, NamedSignalValue):
                            col_defs.append(f'"{sig.name}" TEXT')
                        elif isinstance(test_value, (float, int)):
                            col_defs.append(f'"{sig.name}" REAL')
                        else:
                            col_defs.append(f'"{sig.name}" TEXT')

                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS "{message.name}" (
                        {", ".join(col_defs)}
                    )
                    """
                    self.cur.execute(create_sql)
                    self.tables.add(message.name)

                columns = ['"Timestamp"', '"Source"']
                values = [timestamp, src]

                for sig in message.signals:
                    val = decoded[sig.name]

                    if isinstance(val, NamedSignalValue):
                        val = str(val)

                    columns.append(f'"{sig.name}"')
                    values.append(val)

                    if isinstance(val, (float, int)):
                        if src not in self.numerical:
                            self.numerical[src] = {}
                        if message.name not in self.numerical[src]:
                            self.numerical[src][message.name] = set()
                        self.numerical[src][message.name].add(sig.name)

                placeholders = ', '.join(['?'] * len(values))
                insert_sql = f"""
                INSERT INTO "{message.name}" ({', '.join(columns)})
                VALUES ({placeholders})
                """
                self.cur.execute(insert_sql, values)

        self.conn.commit()

    def get_datasets(self, selected):
        """
        Process selected CAN signals into numpy arrays
        """
        datasets = []

        for src, messages in selected.items():
            for msg, signals in messages.items():
                for sig in signals:
                    query = f"""
                        SELECT Timestamp, "{sig}"
                        FROM {msg}
                        ORDER BY Timestamp ASC
                    """

                    self.cur.execute(query)
                    rows = self.cur.fetchall()

                    timestamps = numpy.array([r[0] for r in rows], dtype=float) / 1000
                    values     = numpy.array([r[1] for r in rows], dtype=float)

                    datasets.append((sig, timestamps, values))

        return datasets
                    
    def export_csv(self):
        print('Export CSV clicked')