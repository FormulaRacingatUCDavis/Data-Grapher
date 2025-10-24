class Model(object):
    def __init__(self):
        self.data = []

    def get_data(self, ts, src, id, msg, data):
        parsed = {}

        parsed['Timestamp'] = ts
        parsed['Source'] = src
        parsed['ID'] = id
        parsed['Message'] = msg
        parsed['Data'] = data

        self.data.append(parsed)