class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class SharePointError(AppError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=500, details=details)

class DataNotFoundError(AppError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=404, details=details)

class ValidationError(AppError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=422, details=details)
