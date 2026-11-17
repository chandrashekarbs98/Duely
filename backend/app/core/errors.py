"""Domain errors.

Services raise these; they know nothing about HTTP. main.py maps each one to a status code,
so the business layer stays reusable (e.g. from the seed script or a scheduled job).
"""


class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class AuthError(AppError):
    status_code = 401


class TooManyRequestsError(AppError):
    status_code = 429


class ServiceUnavailableError(AppError):
    status_code = 503
