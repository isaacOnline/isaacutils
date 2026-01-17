from typing import Dict, List
import logging


def get_post_attr(post_obj: dict, attr: str, post_attr_paths: Dict[str, List[str]]):
    """Extract a single attribute from a Twitter/X post object.

    Navigates nested dictionary paths defined in `post_attr_paths` to extract
    the requested attribute. Handles both standard Tweet objects and
    TweetWithVisibilityResults wrappers.

    "text" attribute extraction returns note_tweet text if available, falling back
    to legacy full_text.

    Args:
        post_obj: A dictionary representing a Tweet or TweetWithVisibilityResults object.
        attr: The attribute name to extract (e.g., "text", "post_id", "lang").
        post_attr_paths: A mapping of attribute names to lists of possible
            dictionary paths within the post object.

    Returns:
        The extracted attribute value, or None if not found or attr is unknown.

    Raises:
        AssertionError: If post_obj is not a recognized tweet type, or if
            multiple paths return conflicting values (except for "text").
    """
    if attr == "__typename":
        return post_obj.get("__typename")
    # TweetWithVisibilityResults has a wrapper around tweet info
    while post_obj.get("__typename") == "TweetWithVisibilityResults":
        post_obj = post_obj.get("tweet", {})
    if attr not in post_attr_paths:
        logging.warning(f"Unkown attr '{attr}'; skipping extraction.")
        return None

    _values = list()
    for _path in post_attr_paths[attr]:
        _path = _path.split(".")
        _cursor = post_obj
        for _part in _path:
            _cursor = _cursor.get(_part, {})
        if type(_cursor) is not dict:
            _values.append(_cursor)

    if not _values:
        return None

    assert len(set(_values)) == 1
    _value = _values[0]
    return _value


def get_post_attrs(post_obj: dict, post_attr_paths: Dict[str, List[str]]):
    """Extract full set of attributes from a Twitter/X post object.

    Args:
        post_obj: A dictionary representing a tweet object.
        post_attr_paths: A mapping of attribute names to lists of possible
            dictionary paths within the post object. Format is: 
                {
                    "attr_name_1": ["path.to.attr1.option1", "path.to.attr1.option2"],
                    "attr_name_2": ["path.to.attr2.option1"],
                    ...
                }

    Returns:
        A dictionary mapping each requested attribute name to its extracted value.
    """
    _results = {}
    for _attr in post_attr_paths.keys():
        _results[_attr] = get_post_attr(post_obj, _attr, post_attr_paths)

    return _results
