from flask import jsonify


class BaseParamsError(Exception):

    def __init__(self, message=None, code=191, status_code=400, payload=None):
        self.status_code = status_code
        self.code = code
        self.payload = payload
        self.message = message

    def _to_dict(self):
        rv = dict(self.payload or ())
        rv['status'] = self.status_code
        rv['code'] = self.code
        rv['message'] = self.message
        return rv


class MissingParams(BaseParamsError):

    def to_dict(self):
        rv = self._to_dict()
        rv['detail'] = "Competition or Season Ids or both is not available!"
        rv['title'] = "Missing competition or season id"
        return rv


class IncorrectParams(BaseParamsError):

    def to_dict(self):
        rv = self._to_dict()
        rv['detail'] = "The given input for parameters do not mach with corresponding functions parameters."
        rv['title'] = "Parameters are incorrect."
        return rv


class ErrorHandler:

    def __init__(self, app):
        self.app = app
        self.handle_error(self.app)

    @staticmethod
    def handle_error(app):

        @app.errorhandler(MissingParams)
        def handle_missing_params(error):
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response

        @app.errorhandler(IncorrectParams)
        def handle_incorrect_params(error):
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response
