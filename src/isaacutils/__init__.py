"""isaacutils: Personal Python utilities for common tasks."""

__version__ = "0.2.2"

from .mail import send_alert, send_html_alert, EmailHandler
from .posts import get_post_attr, get_post_attrs

__all__ = [
    "__version__",
    "send_alert",
    "send_html_alert",
    "EmailHandler",
    "get_post_attr",
    "get_post_attrs",
]
