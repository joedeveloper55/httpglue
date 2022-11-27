class FakeWidgetStore:
    def __init__(self, *args, **kwargs):
        self._storing_dict = {}

    def get_widget(self, w_id):
        return self._storing_dict[w_id]

    def put_widget(self, w):
        self._storing_dict[w.id] = w

    def del_widget(self, w_id):
        del self._storing_dict[w_id]

    def get_widgets(self):
        return self._storing_dict.values()

    def put_widgets(self, ws):
        for w in ws:
            self._storing_dict[w.id] = w

    def del_widgets(self):
        self._storing_dict.clear()