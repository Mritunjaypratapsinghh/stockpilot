from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, message: str, status_code: int = 400, errors: list = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.errors = errors or []


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str = None):
        msg = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        super().__init__(msg, status_code=404)


class ValidationError(AppException):
    def __init__(self, message: str, errors: list = None):
        super().__init__(message, status_code=422, errors=errors)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(AppException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class DuplicateError(AppException):
    def __init__(self, resource: str, identifier: str = None):
        msg = f"{resource} already exists" if not identifier else f"{resource} '{identifier}' already exists"
        super().__init__(msg, status_code=409)


class BusinessLogicError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
