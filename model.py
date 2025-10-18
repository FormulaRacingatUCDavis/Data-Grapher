import cantools.database

class Model(object):
    def __init__(self):
        self.messages = {}
        
        self.canvases = []
        self.figure_handles = []
        self.toolbar_handles = []
        self.tab_handles = []
        self.current_window = -1
        self.graphTabs = []

        self.frucd_dbc = cantools.database.load_file('FE12.dbc')
        self.mc_dbc = cantools.database.load_file('20240129 Gen5 CAN DB.dbc')

    def parse_data(self, datafile):
        pass