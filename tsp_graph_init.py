class LIEU:
    def __init__(self, x, y, name):

        self.x = x
        self.y = y
        self.name = name

    def distance(self, autre_lieu):
        return (self.x - autre_lieu.x, self.y - autre_lieu.y)

