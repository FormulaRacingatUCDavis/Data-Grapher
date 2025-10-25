class Model(object):
    def __init__(self):
        self.data = []
        self.graphable = dict() # {'INV': []}

    def get_data(self, ts, src, id, msg, data):
        """
        Update model with input and track graphable data
        """
        parsed = {}

        parsed['Timestamp'] = ts
        parsed['Source'] = src
        parsed['ID'] = id
        parsed['Message'] = msg
        parsed['Data'] = data

        for signal, value in data.items():
            if not isinstance(value, str):
                if src not in self.graphable:
                    self.graphable[src] = set()
                self.graphable[src].add(signal.replace(f'{src}_', ''))

        self.data.append(parsed)