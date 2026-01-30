from typing import Union

try:
    import polars as pl
except ImportError:
    raise ImportError(
        "polars is required for this module. "
        "Install with: pip install isaacutils[polars]"
    ) from None

from src.isaacutils.constants import X_EPOCH_MILLIS
from src.isaacutils.constants import X_SNFLK_BIT_SHIFT


def snowflake_to_millis(expr: Union[pl.Expr, str, pl.Series]) -> pl.Expr:
    """
    Convert a Twitter/X snowflake ID to a timestamp in milliseconds.

    :param expr: Column expression or name containing snowflake IDs (integers).
    :type expr: IntoExprColumn
    :return: Column expression with timestamps in milliseconds.
    :rtype: pl.Expr
    """
    if isinstance(expr, str):
        expr = pl.col(expr)
    elif isinstance(expr, pl.Series):
        expr = pl.lit(expr)
    return expr.cast(pl.Int64) // (1 << X_SNFLK_BIT_SHIFT) + X_EPOCH_MILLIS