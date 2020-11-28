import io
import sys
import logging

import pandas as pd

from .config import Config
from contextlib import contextmanager
from psycopg2.extras import DictCursor, DictRow
from typing import Optional, Union, Tuple, IO
from psycopg2 import sql, Error, OperationalError, ProgrammingError, \
    DatabaseError
from psycopg2.pool import AbstractConnectionPool, ThreadedConnectionPool, \
    PoolError
from sqlalchemy import create_engine



# Spawn module-level logger
logger = logging.getLogger(__name__)

# Add a human-friendly pretty-print representation of psycopg2 'Pool' objects.
AbstractConnectionPool.__str__ = lambda pool: ("POOL SETTINGS:\n"
                                               "CLOSED:\t{closed}\n"
                                               "MIN_CONNS:\t{minconn}\n"
                                               "MAX_CONNS:\t{maxconn}\n"
                                               "IN_USE:\t{_rused}\n"
                                               ).format(**pool.__dict__)


class Database:
    """Jumbo's abstract PostgreSQL client manager.

    Allows to manage multiple independent connections to a PostgreSQL database
    and to handle arbitrary transactions between clients and database.

    Usage:

        .. code-block:: python

            # Initialize abstract database manager
            database = jumbo.database.Database()

            # Open a connection pool to the PostgreSQL database:
            with database.open() as pool:

                # Use a connection from the pool
                with pool.connect():

                    # Execute SQL query on the database
                    pool.send(SQL_query)

            # context managers ensure connections are properly returned to the
            pool, and that the pool is properly closed.
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        """Initializes manager to handle connections to a given PostgreSQL
        database.

        Args:
            config: jumbo's database configuration settings. Defaults to
                    using settings from the jumbo.env file located in the
                    working directory of the script invoking this constructor.

        Attributes:
            config (jumbo.config.Config):   jumbo's database configuration
                                            settings.
            pool (psycopg2.pool):           connection pool to the PostgreSQL
                                            database. Initially closed.
        """

        # Database configuration settings
        self.config = config if config is not None else Config()
        # initialize a placeholder connection pool
        self.pool = ThreadedConnectionPool(0, 0)
        self.pool.closed = True  # keep it closed on construction

        # Log configuration settings
        logger.info(f"Jumbo Connection Manager created:\n{self.config}")

    @contextmanager
    def open(self, minconns: int = 1, maxconns: Optional[int] = None) -> None:
        """Context manager opening a connection pool to the PostgreSQL
        database. The pool is automatically closed on exit and all
        connections are properly handled.

        Example:

            .. code-block:: python

                with self.open() as pool:

                    # do something with the pool

                # pool is automatically closed here

        Args:
            minconns:   minimum amount of available connections in the pool,
                        created on startup.
            maxconns:   maximum amount of available connections supported by
                        the pool. Defaults to minconns.
        """
        try:

            # Create connection pool
            self.open_pool(minconns, maxconns)

            yield self

        except OperationalError as e:
            logger.error(f"Error while opening connection pool: {e}")

        finally:
            # Close all connections in the pool
            self.close_pool()

    def open_pool(self, minconns: int = 1,
                  maxconns: Optional[int] = None) -> None:
        """Initialises and opens a connection pool to the PostgreSQL database
        (psycopg2.pool.ThreadedConnectionPool).

        'minconn' new connections are created  immediately. The connection pool
        will support a maximum of about 'maxconn' connections.

        Args:
            minconns:   minimum amount of available connections in the pool,
                        created on startup.
            maxconns:   maximum amount of available connections supported by
                        the pool. Defaults to 'minconns'.
        """

        # If the pool hasn't been opened yet
        if self.pool.closed:

            # initialize max number of supported connections
            maxconns = maxconns if maxconns is not None else minconns

            # create a connection pool based on jumbo's configuration settings
            self.pool = ThreadedConnectionPool(
                minconns, maxconns,
                host=self.config.DATABASE_HOST,
                user=self.config.DATABASE_USERNAME,
                password=self.config.DATABASE_PASSWORD,
                port=self.config.DATABASE_PORT,
                dbname=self.config.DATABASE_NAME,
                sslmode='disable')

            logger.info(f"Connection pool created to PostgreSQL database: "
                        f"{maxconns} connections available.")

    def close_pool(self) -> None:
        """Closes all connections in the pool, making it unusable by clients.
        """

        # If the pool hasn't been closed yet
        if not self.pool.closed:
            self.pool.closeall()
            logger.info("All connections in the pool have been closed "
                        "successfully.")

    @contextmanager
    def connect(self, key: int = 1) -> None:
        """Context manager opening a connection to the PostgreSQL database
        using a connection [key] from the pool. The connection is
        automatically closed on exit and all transactions are properly handled.

        Example:

            .. code-block:: python

                # check-out connection from the pool
                with self.connect(key):

                    # do something with the connection e.g.
                    # self.send(sql_query, key)

                # connection is automatically closed here

        Args:
            key (optional): key to identify the connection being opened.
                            Required for proper book keeping.
        """

        # check-out an available connection from the pool
        self.get_connection(key=key)

        try:

            yield self

        except (Exception, KeyboardInterrupt) as e:
            logger.error(f"Error raised during connection [{key}] "
                         f"transactions: {e}")

        finally:
            # return the connection to the pool
            self.put_back_connection(key=key)

    def get_connection(self, key: int = 1) -> None:
        """Connect to a Postgres database using an available connection from
        pool. The connection is assigned to 'key' on checkout.

        Args:
            key (optional): key to assign to the connection being opened.
                            Required for proper book keeping.
        """

        # If a pool has been opened
        if not self.pool.closed:

            try:

                # If the specific connection hasn't been already opened
                if key not in self.pool._used:

                    # Connect to PostgreSQL database
                    self.pool.getconn(key)
                    logger.info(f"Connection retrieved successfully: pool "
                                f"connection [{key}] now in use.")

                    # perform handshake
                    self.on_connection(key)

                else:
                    logger.warning(f"Pool connection [{key}] is already in "
                                   f"use by another client. Try a different "
                                   f"key.")

            except PoolError as error:
                logger.error(f"Error while retrieving connection from "
                             f"pool:\t{error}")
                sys.exit()

        else:
            logger.warning(f"No pool to the PostgreSQL database: cannot "
                           f"retrieve a connection. Try to .open() a pool.")

    def on_connection(self, key: int = 1) -> None:
        """Client-database handshaking script to perform on retrieval of a
        PostgreSQL connection from the pool.

        Args:
            key (optional): key of the pool connection being used in
                            the transaction. Defaults to [1].
        """

        # return database information
        info = self.connection_info(key=key)
        logger.info(f"You are connected to - {info}")

    def put_back_connection(self, key: int = 1) -> None:
        """Puts back a connection in the connection pool.

        Args:
            key (optional): key of the pool connection being used in the
                            transaction. Defaults to [1].
        """

        # If this specific connection is under use
        if key in self.pool._used:

            # Reset connection to neutral state
            self.pool._used[key].reset()
            # Put back connection in the pool
            self.pool.putconn(self.pool._used[key], key)

            logger.info(f"Connection returned successfully: pool connection "
                        f"[{key}] now available again.")

        else:
            logger.warning(f"Pool connection [{key}] has never been opened: "
                           f"cannot put it back in the pool.")

    def send(self,
             query: Union[str, sql.Composed],
             subs: Optional[Tuple[str, ...]] = None,
             cur_method: int = 0,
             file: Optional[IO] = None,
             fetch_method: int = 2,
             key: int = 1) -> Union[DictRow, None]:
        """Sends an arbitrary PostgreSQL query to the PostgreSQL database.
        Transactions are auto-committed on execution.

        Example:

            .. code-block:: python

                # A simple query with no substitutions
                query = 'SELECT * FROM table_name;'
                results = self.send(query)

                # A more complex query with dynamic substitutions
                query = 'INSERT INTO table_name (column_name, another_column_name) VALUES (%s, $s);'
                subs = (value, another_value)
                results = self.send(query, subs)

        Args:
            query:                      PostgreSQL command string (can be
                                        template with psycopg2 %s fields).
            subs (optional):            tuple of values to substitute in SQL
                                        query  template (cf. psycopg2 %s
                                        formatting)
            cur_method (optional):      code to select which psycopg2 cursor
                                        execution method to use for the SQL
                                        query:
                                        0:  cursor.execute()
                                        1:  cursor.copy_expert()
            file (optional):            file-like object to read or write to
                                        (only relevant if cur_method:1).
            fetch_method (optional):    code to select which psycopg2 result
                                        retrieval method to use (fetch*()):
                                        0: cur.fetchone()
                                        2: cur.fetchall()
            key (optional):             key of the pool connection being used
                                        in the transaction. Defaults to [1].

        Returns:
            list of query results (if any). Can be accessed as dictionaries.
        """

        # If this specific connection has already been opened
        if key in self.pool._used:

            try:  # try running a transaction

                with self.pool._used[key].cursor(
                        cursor_factory=DictCursor) as cur:

                    # Bind arguments to query string (if present)
                    if subs is not None:
                        query = cur.mogrify(query, subs)
                    else:
                        query = cur.mogrify(query)

                    # Execute query
                    if cur_method == 0:
                        cur.execute(query)
                    elif cur_method == 1:
                        cur.copy_expert(sql=query, file=file)

                    # Fetch query results
                    try:
                        if fetch_method == 0:
                            records = cur.fetchone()
                        elif fetch_method == 2:
                            records = cur.fetchall()
                    # Handle SQL queries that don't return any results
                    # (INSERT, UPDATE, etc...)
                    except ProgrammingError:
                        records = []
                        pass

                    # Commit transaction
                    self.pool._used[key].commit()

                    # Display success message (and shorten query if too long)
                    s_query = query
                    if len(query) > 78:
                        s_query = (str(query[:75]) + '...')
                    success_msg = f"Successfully sent: {s_query} "
                    if cur.rowcount >= 0:
                        success_msg += f": {cur.rowcount} rows affected."
                    logger.info(success_msg)

                    return records  # dictionaries

            except (Exception, Error, DatabaseError) as e:
                # Rollback transaction if any problem
                self.pool._used[key].rollback()
                logger.error(f"Error while sending query {query}:{e}. "
                             f"Transaction rolled-back.")

        else:
            logger.warning(f"Pool connection [{key}] has never been opened: "
                           f"not available for transactions.")

    def listen_on_channel(self, channel_name: str, key: int = 1) -> None:
        """Subscribes to a PostgreSQL notification channel by listening for
        NOTIFYs.

        .. code-block:: postgresql

            -- Command executed:
            LISTEN channel_name;

        Args:
            channel_name:   channel on which to LISTEN. PostgreSQL database
                            should be configured to send NOTIFYs on this
                            channel.
            key (optional): key of the pool connection being used in the
                            transaction. Defaults to [1].
        """

        query = "LISTEN " + channel_name + ";"
        self.send(query, key=key)

    def connection_info(self, key: int = 1) -> DictRow:
        """Fetches PostgreSQL database version.

        .. code-block:: postgresql

            -- Command executed:
            SELECT version();

        Args:
            key (optional): key of the pool connection being used in the
                            transaction. Defaults to [1].

        Returns:
            query result. Contains PostgreSQL database version information.
        """

        query = "SELECT version();"
        info = self.send(query, fetch_method=0, key=key)  # fetchone()
        return info

    def copy_to_table(self, query: sql.Composed, file: IO, db_table: str,
                      replace: bool = True, key: int = 1) -> None:
        """Utility wrapper to send a SQL query to copy data to database table.
        Allows to replace table if it already exists in the database.

        .. code-block:: postgresql

            -- Command type expected:
            COPY table_name [ ( column_name [, ...] ) ]
                FROM STDIN
                [ [ WITH ] ( option [, ...] ) ]

            -- Ancillary command pre-executed:
            TRUNCATE table_name;

        Example:

            .. code-block:: python

                # Copy csv data from file to a table in the database
                query = "COPY table_name FROM STDIN WITH CSV DELIMITER '\\t'"
                results = self.copy_to_table(query, file="C:\\data.csv",
                                             db_table='table_name')


        Args:
            query:              PostgreSQL COPY command string.
            file:               absolute path to file-like object to read data
                                from.
            db_table:           the name (optionally schema-qualified) of an
                                existing database table.
            replace (optional): replaces table contents if True. Appends data
                                to table contents otherwise.
            key (optional):     key of the pool connection being used in the
                                transaction. Defaults to [1].
        """

        # Replace the table already existing in the database
        if replace:
            # pass table name dynamically to query
            query_tmp = sql.SQL(
                "TRUNCATE {};").format(sql.Identifier(db_table))
            self.send(query_tmp, key=key)

        # Copy the table from file (cur_method:1 = cur.copy_expert)
        self.send(query, cur_method=1, file=file, key=key)

    def copy_df(self, df: pd.DataFrame, db_table: str, replace: bool = True,
                key: int = 1) -> None:
        """Utility wrapper to efficiently copy a pandas.DataFrame to a
        PostgreSQL database table.

        This method is faster than panda's native *.to_sql()* method and
        exploits PostgreSQL COPY TO command. Provides a useful mean of saving
        results from a pandas-centred data analysis pipeline directly to the
        database.

        Args:
            df:                 dataframe to be copied.
            db_table:           the name (optionally schema-qualified) of the
                                table to write to.
            replace (optional): replaces table contents if True. Appends data
                                to table contents otherwise.
            key (optional):     key of the pool connection being used in the
                                transaction. Defaults to [1].
        """

        if key in self.pool._used:

            try:
                # Create headless csv from pandas dataframe
                io_file = io.StringIO()
                df.to_csv(io_file, sep='\t', header=False, index=False)
                io_file.seek(0)

                # Quickly create a table with correct number of columns / data
                # types Unfortunately we will need to quickly build a
                # sqlalchemy engine for this hack to work
                replacement_method = 'replace' if replace else 'append'
                engine = create_engine('postgresql+psycopg2://',
                                       creator=lambda: self.pool._used[key])
                df.head(0).to_sql(db_table, engine,
                                  if_exists=replacement_method, index=False)

                # But then exploit postgreSQL COPY command instead of slow
                # pandas .to_sql(). Note that replace is set to false in
                # copy_table as we want to preserve the header table created
                # above
                sql_copy_expert = sql.SQL(
                    "COPY {} FROM STDIN WITH CSV DELIMITER '\t'").format(
                    sql.Identifier(db_table))
                self.copy_to_table(sql_copy_expert, file=io_file,
                                   db_table=db_table, replace=False, key=key)

                logger.info(f"DataFrame copied successfully to PostgreSQL "
                            f"table.")

            except (Exception, DatabaseError) as error:
                logger.error(f"Error while copying DataFrame to PostgreSQL "
                             f"table: {error}")

        else:
            logger.warning(f"Pool connection [{key}] has never been opened: "
                           f"cannot use it to copy Dataframe to database.")
