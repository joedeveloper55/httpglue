class Widget:
    def __init__(self, id, name, num_of_parts):
        # add validation logic
        # maybe also just make this a dataclass
        self.id = id
        self.name = name
        self.num_of_parts = num_of_parts

    @classmethod
    def from_ds(cls, ds):
        return cls(**ds)

    def to_ds(self):
        return {
            'id': self.id,
            'name': self.name,
            'num_of_parts': self.num_of_parts
        }