from sys import exit


name = "umptag"

class Umptag:
    @classmethod
    def initialize_umptag(cls, attribute, tablename=None):
        self.attribute = attribute
        if tablename is None:
            tablename = self.attribute
        # Hm!!
        raise NotImplementedError

