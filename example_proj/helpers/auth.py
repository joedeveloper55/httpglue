import abc
import base64
import hashlib

import psycopg


class AuthenticationError(Exception):
    def __init__(self, details):
        super().__init__('Authentication Error')
        self.details = details


class BasicAuthHelper:
    def __init__(self, auth_provider):
        '''
        Initialize a BasicAuthHerlper

        :param AuthProvider auth_provider: an object that supplies
           the authentication and possibly authorization
           logic for the BasicAuthHelper. It is how the user
           is actually authenticated against the password.
        '''
        self.auth_provider = auth_provider

    def authenticate(self, req):
        '''
        Authenticate and maybe authorize a request using basic auth.
        The function can return anything, and you can use this to
        indicate which 'privelidges' a request is authorized as
        having. If the request could not be authentciated, this should
        raise an AuthenticationError

        :param httpglue.Request req: the request to authenticate

        :raises AuthenticationError: on authentication error

        :rtype: mixed
        '''
        if 'Authorization' not in req.headers:
            raise AuthenticationError({
                'was_unexpected_error': True,
                'unexpected_error': 'no_authorization_header_present',
                'username': {
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
                'was_unexpected_error': True,
                'unexpected_error': 'authorization_header_malformed',
                'username': {
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
                'was_unexpected_error': True,
                'unexpected_error': 'unsupported_authorization_method',
                'username': {
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
                'was_unexpected_error': True,
                'unexpected_error': 'invalid_base64_encoding_of_credentials',
                'username': {
                    'supplied': None,
                    'was_valid': False
                },
                'password': {
                    'supplied': None,
                    'was_Valid': False
                }
            })

        if not len(b64_decoded_credentials.split(b':')) == 2:
            raise AuthenticationError({
                'was_unexpected_error': True,
                'unexpected_error': 'authorization_header_malformed',
                'username': {
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

        return self.auth_provider.authenticate_creds(
            username,
            password
        )


class AuthProvider(abc.ABC):

    @abc.abstractmethod
    def authenticate_creds(self, username, password):
        '''
        You override this function to implement your credential
        check.

        It should raise an authentication error if the credentials
        are bad.

        It can return any value of any type. This can be used to
        communicate which things a given authenticated user is
        authorized to do. For example, you could return a set of
        strings indicating the 'privelidges' that a given
        authenticated user has.

        :param str username: the username
        :param str password: the password

        :raises AuthenticationError: on auth failure or error

        :rtype: mixed
        '''
        pass


class DBUserPassCredsAuthProvider(AuthProvider):
    def __init__(self, db_conn_pool):
        self._db_conn_pool = db_conn_pool

    def _query_db(self, sql, params, fetch_items=False):
        with self._db_conn_pool.connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as curs:
                curs.execute(sql, params)
                if fetch_items:
                    return curs.fetchall()

    def authenticate_creds(self, username, password):
        results = self._query_db(
            """
            SELECT username,
                   password_hash,
                   password_salt
              FROM public.widgets_api_users
             WHERE username = %(username)s;
            """,
            {'username': username},
            fetch_items=True
        )

        if len(results) == 0:
            raise AuthenticationError({
                'was_unexpected_error': False,
                'unexpected_error': None,
                'username': {
                    'supplied': username,
                    'was_valid': False
                },
                'password': {
                    'supplied': password,
                    'was_Valid': False
                }
            })
        else:
            # WARNING: you should not use sha512 for most
            # security purposes and instead opt for something
            # like bcrypt for storing your passwords in a db.
            # We used sha512 here becuase this is just a simple
            # exemplar and ease of installation and running is
            # more important here than bulletproof security,
            # and using a standardlib module like hashlib
            # was prefferred over something more complex to install
            # (bcrypt).
            hashed_n_salted_password = hashlib.sha512(
                password.encode('utf-8') +
                results[0]['password_salt'].encode('utf-8')
            ).hexdigest()
            if hashed_n_salted_password == results[0]['password_hash']:
                return  # authenticated
            else:
                raise AuthenticationError({
                    'was_unexpected_error': False,
                    'unexpected_error': None,
                    'username': {
                        'supplied': username,
                        'was_valid': True
                    },
                    'password': {
                        'supplied': password,
                        'was_valid': False
                    }
                })
