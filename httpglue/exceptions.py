# Copyright 2021, Joseph P McAnulty

class NoMatchingPathError(Exception):
    def __init__(self, path, path_specs):
        message = f'The path {path} did not match any of {path_specs}'
        super().__init__(message)


class NoMatchingMethodError(Exception):
    def __init__(self, method, path, allowed_methods, matching_path_specs):
        message = (
            f'The {method} method is not one of the allowed methods {allowed_methods} '
            f'on {path} (matching path specs: {matching_path_specs})'
        )
        super().__init__(message)
        self.method = method
        self.path = path
        self.allowed_methods = allowed_methods
        self.matching_path_specs = matching_path_specs


class NoMatchingPredError(Exception):
    def __init__(self, method, path, matching_method_spec_path_spec_pairs, failed_predicates):
        message = f'The {method} {path} request nearly matched some endpoints, but failed due to predicates'
        self.method = method
        self.path = path
        self.matching_method_spec_path_spec_pairs = matching_method_spec_path_spec_pairs
        self.failed_predicates = failed_predicates


class WSGIRequestMappingError(Exception):
    def __init__(self):
        message = (
            'an httpglue.Req object could not be made from the wsgi callable. '
            'this is probably a framework bug, a bug in the wsgi server '
            'you\'re running your app in, or some system error'
        )
        super().__init__(message)


class WSGIResponseMAppingError(Exception):
    def __init__(self):
        message = (
            'an httpglue.Res object could not be used by the wsgi callable '
            'to make a response to the requester. '
            'this is probably a framework bug, a bug in the wsgi server '
            'you\'re running your app in, or some system error'
        )
        super().__init__(message)
