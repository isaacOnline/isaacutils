"""isaacutils: Personal Python utilities for common tasks."""

__version__ = "0.3.0"

from .mail import send_alert, send_html_alert, EmailHandler
from .posts import get_post_attr, get_post_attrs
from .str import camel_to_snake, remove_urls

__all__ = [
    "__version__",
    "send_alert",
    "send_html_alert",
    "EmailHandler",
    "get_post_attr",
    "get_post_attrs",
    "camel_to_snake",
    "remove_urls",
]
