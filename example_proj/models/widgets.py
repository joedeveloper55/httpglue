class Widget:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, val):
        if type(val) != int:
            raise TypeError(
                'id property must be of type int, not '
                '%s' % type(val))
        self._id = val

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        if type(val) != str:
            raise TypeError(
                'name property must be of type str, not '
                '%s' % type(val))
        self._name = val

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, val):
        if type(val) != str:
            raise TypeError(
                'description property must be of type str, not '
                '%s' % type(val))
        self._description = val

    @classmethod
    def fromdict(cls, d):
        return cls(**d)

    def asdict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }