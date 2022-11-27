import abc
import base64


class AuthenticationError(Exception):
    def __init__(self, details):
        super().__init__('The supplied credentials were invalid')
        self.details = details


class BasicAuthHelper(abc.ABC):

    def authenticate(self, req):
        '''
        Authenticate and authorize a request.
        The function can return anything, and you can use this to
        indicate which 'privelidges' a request is authorized as
        having. If the request could not be authentciated, this should
        raise an AuthenticationError
        '''
        if 'Authorization' not in req.headers:
            raise AuthenticationError({
                'was_unecpected_error': True,
                'unexpected_error': 'no_authorization_header_present',
                'uname': {
                    'supplied': None,
                    'was_valid': False
                },
                'password': {
                    'supplied': None,
                    'was_Valid': False
                }
            })

        if not len(req.headers['Authorization'].split(' ')) == 2:
            raise AuthenticationError({
                'was_unecpected_error': True,
                'unexpected_error': 'authorization_header_malformed',
                'uname': {
                    'supplied': None,
                    'was_valid': False
                },
                'password': {
                    'supplied': None,
                    'was_Valid': False
                }
            })
        else:
            auth_method, credentials = req.headers['Authorization'].split(' ')

        if not auth_method == 'Basic':
            raise AuthenticationError({
                'was_unecpected_error': True,
                'unexpected_error': 'unsupported_authorization_method',
                'uname': {
                    'supplied': None,
                    'was_valid': False
                },
                'password': {
                    'supplied': None,
                    'was_Valid': False
                }
            })

        try:
            b64_decoded_credentials = base64.b64decode(credentials)
        except Exception:
            raise AuthenticationError({
                'was_unecpected_error': True,
                'unexpected_error': 'invalid_base64_encoding_of_credentials',
                'uname': {
                    'supplied': None,
                    'was_valid': False
                },
                'password': {
                    'supplied': None,
                    'was_Valid': False
                }
            })

        if not len(b64_decoded_credentials.split(b':')) == 2:
            print(b64_decoded_credentials)
            print('JELLYSTAINS')
            raise AuthenticationError({
                'was_unecpected_error': True,
                'unexpected_error': 'authorization_header_malformed',
                'uname': {
                    'supplied': None,
                    'was_valid': False
                },
                'password': {
                    'supplied': None,
                    'was_Valid': False
                }
            })
        else:
            username, password = b64_decoded_credentials.split(b':')
            username = username.decode('utf-8')
            password = password.decode('utf-8')

        return self.authenticate_creds(username, password)

    @abc.abstractmethod
    def authenticate_creds(self, uname, password):
        pass


class DummyBasicAuthHelper(BasicAuthHelper):
    def __init__(self, trust=False):
        self.trust = trust

    def authenticate_creds(self, uname, password):
        if self.trust:
            return
        else:
            raise AuthenticationError({
                'was_unecpected_error': False,
                'unexpected_error': None,
                'uname': {
                    'supplied': uname,
                    'was_valid': False
                },
                'password': {
                    'supplied': password,
                    'was_Valid': False
                }
            })
