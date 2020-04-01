import io
import sys

from contextlib import contextmanager
from loguru import logger
from psycopg2 import sql, Error, OperationalError, ProgrammingError, DatabaseError
from psycopg2.extras import DictCursor
from psycopg2.pool import AbstractConnectionPool, ThreadedConnectionPool, PoolError
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from .config import Config


# Add a human-friendly pretty-print representation of psycopg2 'Pool' objects.
AbstractConnectionPool.__str__ = lambda pool: ("POOL SETTINGS:\n"
                                               "CLOSED:\t{closed}\n"
                                               "MIN_CONNS:\t{minconn}\n"
                                               "MAX_CONNS:\t{maxconn}\n"
                                               "IN_USE:\t{_rused}\n"
                                               ).format(**pool.__dict__)


class Database:
    """Jumbo's abstract PostgreSQL client manager.

    Allows to manage multiple independent connections to a PostgreSQL database and to handle arbitrary transactions
    between clients and database.

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

            # context managers ensure connections are properly returned to the pool, and that the pool is properly
            # closed.
    """

    def __init__(self, config=None):
        """Initializes manager to handle connections to a given PostgreSQL database.

        Args:
            config (jumbo.config.Config, optional): jumbo's database configuration settings. Defaults to using settings
                                                    from the .env file located in the working directory of the script
                                                    invoking this constructor.

        Attributes:
            config (jumbo.config.Config):   jumbo's database configuration settings.
            pool (psycopg2.pool):           connection pool to the PostgreSQL database. Initially closed.

        """

        self.config = config if config is not None else Config()  # database connection settings
        self.pool = ThreadedConnectionPool(0, 0)  # initialize a placeholder connection pool
        self.pool.closed = True  # keep it closed on construction

        # Log configuration settings
        logger.debug(f"Jumbo Connection Manager created:\n{self.config}")

    @contextmanager
    def open(self, minconns=1, maxconns=None):
        """Context manager opening a connection pool to the PostgreSQL database. The pool is
        automatically closed on exit and all connections are properly handled.

        Example:

            .. code-block:: python

                with self.open() as pool:

                    # do something with the pool

                # pool is automatically closed here

        Args:
            minconns (int):             minimum amount of available connections in the pool, created on startup.
            maxconns (int, optional):    maximum amount of available connections supported by the pool.
                                        Defaults to minconns.
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

    def open_pool(self, minconns=1, maxconns=None):
        """Initializes and opens a connection pool to the PostgreSQL database (psycopg2.pool.ThreadedConnectionPool).

        'minconn' new connections are created  immediately. The connection pool will support a maximum of about
        'maxconn' connections.

        Args:
            minconns (int):             minimum amount of available connections in the pool, created on startup.
            maxonns (int, optional):    maximum amount of available connections supported by the pool.
                                        Defaults to minconns.
        """

        # If the pool hasn't been opened yet
        if self.pool.closed:

            maxconns = maxconns if maxconns is not None else minconns  # initialize max number of supported connections

            # create a connection pool based on jumbo's configuration settings
            self.pool = ThreadedConnectionPool(minconns, maxconns,
                                               host=self.config.DATABASE_HOST,
                                               user=self.config.DATABASE_USERNAME,
                                               password=self.config.DATABASE_PASSWORD,
                                               port=self.config.DATABASE_PORT,
                                               dbname=self.config.DATABASE_NAME,
                                               sslmode='disable')

            logger.success(f"Connection pool created to PostgreSQL database: {maxconns} connections available.")

    def close_pool(self):
        """Closes all connections in the pool, making it unusable by clients."""

        # If the pool hasn't been closed yet
        if not self.pool.closed:
            self.pool.closeall()
            logger.success("All connections in the pool have been closed successfully.")

    @contextmanager
    def connect(self, key=1):
        """Context manager opening a connection to the PostgreSQL database using a connection [key] from the pool.
        The connection is automatically closed on exit and all transactions are properly handled.

        Example:

            .. code-block:: python

                # check-out connection from the pool
                with self.connect(key):

                    # do something with the connection e.g.
                    # self.send(sql_query, key)

                # connection is automatically closed here

        Args:
            key (int):  key to identify the connection being opened. Required for proper book keeping.
        """

        # check-out an available connection from the pool
        self.get_connection(key=key)

        try:

            yield self

        except (Exception, KeyboardInterrupt) as e:
            logger.error(f"Error raised during connection [{key}] transactions: {e}")

        finally:
            # return the connection to the pool
            self.put_back_connection(key=key)

    def get_connection(self, key=1):
        """Connect to a Postgres database using an available connection from pool. The connection is assigned to 'key'
        on checkout.

        Args:
            key (int):  key to assign to the connection being opened. Required for proper book keeping.
        """

        # If a pool has been opened
        if not self.pool.closed:

            try:

                # If the specific connection hasn't been already opened
                if key not in self.pool._used:

                    # Connect to PostgreSQL database
                    self.pool.getconn(key)
                    logger.success(f"Connection retrieved successfully: pool connection [{key}] now in use.")

                    # perform handshake
                    self.on_connection(key)

                else:
                    logger.warning(f"Pool connection [{key}] is already in use by another client. Try a different key.")

            except PoolError as error:
                logger.error(f"Error while retrieving connection from pool:\t{error}")
                sys.exit()

        else:
            logger.warning(f"No pool to the PostgreSQL database: cannot retrieve a connection. Try to .open() a pool.")

    def on_connection(self, key=1):
        """Client-database handshaking script to perform on retrieval of a PostgreSQL connection from the pool.

        Args:
            key (int, optional):  key of the pool connection being used in the transaction. Defaults to [1].
        """

        # return database information
        info = self.connection_info(key=key)
        logger.info(f"You are connected to - {info}")

    def put_back_connection(self, key=1):
        """Puts back a connection in the connection pool.

        Args:
            key (int, optional):  key of the pool connection being used in the transaction. Defaults to [1].
        """

        # If this specific connection is under use
        if key in self.pool._used:

            # Reset connection to neutral state
            self.pool._used[key].reset()
            # Put back connection in the pool
            self.pool.putconn(self.pool._used[key], key)

            logger.success(f"Connection returned successfully: pool connection [{key}] now available again.")

        else:
            logger.warning(f"Pool connection [{key}] has never been opened: cannot put it back in the pool.")

    def send(self, query, subs=None, cur_method=0, file=None, fetch_method=2, key=1):
        """Sends an arbitrary PostgreSQL query to the PostgreSQL database. Transactions are auto-commited on execution.

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
            query (string or Composed): PostgreSQL command string (can be template with psycopg2 %s fields).
            subs (tuple or None):       tuple of values to substitute in SQL query template (cf. psycopg2 %s formatting)
            cur_method (int):           code to select which psycopg2 cursor execution method to use for the SQL query:
                                        0:  cursor.execute()
                                        1:  cursor.copy_expert()
            file (file):                file-like object to read or write to (only relevant if cur_method:1).
            fetch_method (int):         code to select which psycopg2 result retrieval method to use (fetch*()):
                                        0: cur.fetchone()
                                        2: cur.fetchall()
            key (int):                  key of the pool connection being used in the transaction. Defaults to [1].

        Returns:
            psycopg2.extras.DictRow: list of query results (if any). Can be accessed as dictionaries.
        """

        # If this specific connection has already been opened
        if key in self.pool._used:

            try:  # try running a transaction

                with self.pool._used[key].cursor(cursor_factory=DictCursor) as cur:
                    query = cur.mogrify(query, subs) if subs is not None else cur.mogrify(query)

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
                    # Handle SQL queries that don't return any results (INSERT, UPDATE, etc...)
                    except ProgrammingError:
                        records = []
                        pass

                    # Commit transaction
                    self.pool._used[key].commit()

                    # Display success message
                    s_query = (str(query[:75]) + '...') if len(query) > 78 else query  # shorten query if too long
                    success_msg = f"Successfully sent: {s_query} "
                    if cur.rowcount >= 0:
                        success_msg += f": {cur.rowcount} rows affected."
                    logger.success(success_msg)

                    return records  # dictionaries

            except (Exception, Error, DatabaseError) as e:
                self.pool._used[key].rollback()  # Rollback transaction if any problem
                logger.error(f"Error while sending query {query}:{e}. Transaction rolled-back.")

        else:
            logger.warning(f"Pool connection [{key}] has never been opened: not available for transactions.")

    def listen_on_channel(self, channel_name, key=1):
        """Subscribes to a PostgreSQL notification channel by listening for NOTIFYs.

        .. code-block:: postgresql

            -- Command executed:
            LISTEN channel_name;

        Args:
            channel_name (string):  channel on which to LISTEN. PostgreSQL database should be configured to send NOTIFYs
                                    on this channel.
            key (int):              key of the pool connection being used in the transaction. Defaults to [1].
        """

        query = "LISTEN " + channel_name + ";"
        self.send(query, key=key)

    def connection_info(self, key=1):
        """Fetches PostgreSQL database version.

        .. code-block:: postgresql

            -- Command executed:
            SELECT version();

        Args:
            key (int):              key of the pool connection being used in the transaction. Defaults to [1].

        Returns:
            psycopg2.extras.DictRow: query result. Contains PostgreSQL database version information.
        """

        query = "SELECT version();"
        info = self.send(query, fetch_method=0, key=key)  # fetchone()
        return info

    def copy_to_table(self, query, file, db_table, replace=True, key=1):
        """Utility wrapper to send a SQL query to copy data to database table. Allows to replace table if it already
        exists in the database.

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
                results = self.copy_to_table(query, file="C:\\data.csv", db_table='table_name')


        Args:
            query (string):             PostgreSQL COPY command string, as expected above.
            file (file):                absolute path to file-like object to read data from.
            db_table (string):          the name (optionally schema-qualified) of an existing database table.
            replace (bool, optional):   replaces table contents if True. Appends data to table contents otherwise.
            key (int):              key of the pool connection being used in the transaction. Defaults to [1].
        """

        # Replace the table already existing in the database
        if replace:
            query_tmp = sql.SQL("TRUNCATE {};").format(sql.Identifier(db_table))  # pass dynamic table name to query
            self.send(query_tmp, key=key)

        # Copy the table from file
        self.send(query, cur_method=1, file=file, key=key)  # cur_method:1 = cur.copy_expert

    def copy_df(self, df, db_table, replace=True, key=1):
        """Utility wrapper to efficiently copy a pandas.DataFrame to a PostgreSQL database table.

        This method is faster than panda's native *.to_sql()* method and exploits PostgreSQL COPY TO command. Provides a
        useful mean of saving results from a pandas-centred data analysis pipeline directly to the database.

        Args:
            df (pandas.DataFrame):      dataframe to be copied.
            db_table (string):          the name (optionally schema-qualified) of the table to write to.
            replace (bool, optional):   replaces table contents if True. Appends data to table contents otherwise.
            key (int):                  key of the pool connection being used in the transaction. Defaults to [1].
        """

        if key in self.pool._used:

            try:
                # Create headless csv from pandas dataframe
                io_file = io.StringIO()
                df.to_csv(io_file, sep='\t', header=False, index=False)
                io_file.seek(0)

                # Quickly create a table with correct number of columns / data types
                # We will need to quickly build a sqlalchemy engine for this hack to work
                replacement_method = 'replace' if replace else 'append'
                engine = create_engine('postgresql+psycopg2://', creator=lambda: self.pool._used[key],
                                       poolclass=NullPool)  # NullPool so that we don't interfere with our own pool
                df.head(0).to_sql(db_table, engine, if_exists=replacement_method, index=False)

                # But then exploit postgreSQL COPY command instead of slow pandas .to_sql()
                # Not that replace is set to false in copy_table as we want to preserve the header table created above
                sql_copy_expert = sql.SQL("COPY {} FROM STDIN WITH CSV DELIMITER '\t'").format(sql.Identifier(db_table))
                self.copy_to_table(sql_copy_expert, file=io_file, replace=False, key=key)

                logger.success(f"DataFrame copied successfully to PostgreSQL table.")

            except (Exception, DatabaseError) as error:
                logger.error(f"Error while copying DataFrame to PostgreSQL table: {error}")

        else:
            logger.warning(f"Pool connection [{key}] has never been opened: cannot use it to copy Dataframe to "
                           f"database.")
