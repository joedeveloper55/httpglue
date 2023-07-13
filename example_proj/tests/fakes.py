import contextlib

import helpers.auth


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


class FakeAuthProvider(helpers.auth.AuthProvider):
    def __init__(self, *args, **kwargs):
        self.trust = True

    @contextlib.contextmanager
    def triggered_failure(self):
        previous_trust = self.trust
        try:
            self.trust = False
            yield
        finally:
            self.trust = previous_trust

    def authenticate_creds(self, username, password):
        if self.trust:
            return  # authenticated
        else:
            raise helpers.auth.AuthenticationError({
                'was_unexpected_error': False,
                'unexpected_error': None,
                'uname': {
                    'supplied': username,
                    'was_valid': False
                },
                'password': {
                    'supplied': password,
                    'was_Valid': False
                }
            })
