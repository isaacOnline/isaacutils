
import re

from urlextract import URLExtract  # type: ignore[import-untyped]


def camel_to_snake(text: str) -> str:
    """Convert a camelCase string to snake_case.

    Args:
        text: A camelCase string.

    Returns:
        The string converted to snake_case.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()


def remove_urls(text: str) -> str:
    """Remove all URLs from a string using urlextract.

    Args:
        text: Input text containing URLs.

    Returns:
        Text with all URLs removed and extra whitespace cleaned up.
    """
    extractor = URLExtract()
    for url in extractor.find_urls(text):
        text = text.replace(url, "")
    return " ".join(text.split())
