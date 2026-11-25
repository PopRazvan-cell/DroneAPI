"""Domain exceptions and their RFC 9457 representation."""

from __future__ import annotations

from typing import Any


class AgriDroneError(Exception):
    """Base class for expected application errors."""

    status_code: int = 500
    title: str = "Internal Server Error"
    problem_type: str = "about:blank"

    def __init__(
        self,
        detail: str | None = None,
        *,
        headers: dict[str, str] | None = None,
        **extensions: Any,
    ) -> None:
        self.detail = detail or self.title
        self.headers = headers or {}
        self.extensions = extensions
        super().__init__(self.detail)

    def to_problem(self, *, instance: str | None = None) -> dict[str, Any]:
        """Build an RFC 9457 ``application/problem+json`` document."""
        problem: dict[str, Any] = {
            "type": self.problem_type,
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
        }
        if instance is not None:
            problem["instance"] = instance
        problem.update(self.extensions)
        return problem


class UnauthorizedError(AgriDroneError):
    status_code = 401
    title = "Unauthorized"
    problem_type = "https://agridrone.dev/problems/unauthorized"


class ForbiddenError(AgriDroneError):
    status_code = 403
    title = "Forbidden"
    problem_type = "https://agridrone.dev/problems/forbidden"


class NotFoundError(AgriDroneError):
    status_code = 404
    title = "Not Found"
    problem_type = "https://agridrone.dev/problems/not-found"


class ConflictError(AgriDroneError):
    status_code = 409
    title = "Conflict"
    problem_type = "https://agridrone.dev/problems/conflict"


class InvalidInputError(AgriDroneError):
    status_code = 422
    title = "Unprocessable Entity"
    problem_type = "https://agridrone.dev/problems/invalid-input"


class StorageError(AgriDroneError):
    status_code = 500
    title = "Storage Error"
    problem_type = "https://agridrone.dev/problems/storage"


class ConfigurationError(AgriDroneError):
    status_code = 500
    title = "Configuration Error"
    problem_type = "https://agridrone.dev/problems/configuration"


class NotImplementedFeatureError(AgriDroneError):
    status_code = 501
    title = "Not Implemented"
    problem_type = "https://agridrone.dev/problems/not-implemented"
