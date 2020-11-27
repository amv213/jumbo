"""
Utility functions for jumbo SQL library.
"""

import logging
import pandas as pd

# Spawn module-level logger
logger = logging.getLogger(__name__)


def convert_to_df(results):
    """Converts SQL query results to a pandas DataFrame.

    Args:
        results (psycopg2.extras.DictRow): results fetched from the PostgreSQL database following a SQL query.

    Returns:
        pandas.DataFrame: pandas DataFrame with query results.
    """

    # Take first results row and make column labels out of keys
    columns = [k for k in results[0].keys()] if len(results) > 0 else []
    # Generate pandas DataFrame
    df = pd.DataFrame(results, columns=columns)
    logger.info(f"Successful conversion to DataFrame:\n{df.head()}")
    return df
