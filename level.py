class Level():
    """ Used by the save / loading of levels """
    def __init__(self):
        self.starting_location = (0, 0)
        self.finish_line = (0, 0)
        self.segments = []
        self.polys = []
        self.circles = []