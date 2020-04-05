.. _demos:


************
Demos
************

You will find here a collection of detailed code examples guiding you through core jumbo features. If it's your first
time using jumbo, you are strongly suggested to follow the tutorials in order. If you are an experienced jumbo user feel
free to skip to the section you need a refresher on. These tutorials are an excellent introduction to the library and
will help build familiarity with its syntax and usage protocols.

============
Hello World
============

In this tutorial you will learn how to write jumbo's Hello World!

First things first:

- make sure you have a PostgreSQL server available, and a user account to connect to it.
- make sure you have a properly configured jumbo.env file in the root directory of this notebook

   .. code-block::

         DATABASE_HOST = <my_database_host_address>
         DATABASE_USERNAME = <my_database_user_name>
         DATABASE_PASSWORD = <my_database_user_password>
         DATABASE_PORT = <my_database_port>
         DATABASE_NAME = <my_database_name>

- make sure your user account has appropriate permissions on the database tables you will access

At this point we can start using the library:

   .. code-block:: python

        import jumbo

Jumbo's Database Object
---------------------------

Jumbo automatically populates our database connection parameters in a Config object. Let's have a look:

   .. code-block:: python

        config = jumbo.config.Config()
        print(config)

Now that we have checked that everything is initialized correctly we can create one of the most important objects in the
jumbo library: the Database object (database.Database). The database object is jumbo's representation of the database we
want to connect to. This object will allow us to create connections to the real PostgreSQL server and will automatically
manage all transactions with it. Creating a Database is extremely simple:

   .. code-block:: python

        database = jumbo.database.Database(config)

A one-liner we could put at the beginning of any jumbo script is thus:

   .. code-block:: python

        database = jumbo.database.Database(jumbo.config.Config())

You can also choose to have your .env file in a single private location, instead of always placing a copy in your
current working directory. In that case pass the path to the directory containing your .env file on construction of the
Config object:

   .. code-block:: python

        my_env_path = "D:\\dumbo\\secret"  # jumbo.env is in 'secret' directory
        config = jumbo.config.Config(my_env_path)
        database = jumbo.database.Database(config)

Connection Pools
--------------------

At this point we would like to connect to the database. In general, opening and closing multiple connections to a database creates a bit of overhead - it's more efficient to first initialize a so called connection-pool of *x* connections from which clients can take and put back individual connections as they need them. In jumbo we do this in this way:

   .. code-block:: python

    # Create a connection pool. Context manager ensures pool is closed at the end.
    with database.open() as pool:

        loguru.logger.info("Opened a connection pool.")

        loguru.logger.debug(pool.pool)

The context-manager structure ensures behind the scenes that the connection pool is opened correctly and closed successfully at the end of the script.

Note that in the above example we opened a connection pool containing a single connection, but we can open pools with a minimum and maximum number of available connections using the *minconns* and *maxconns* arguments. The pool will intialize with a minimum amount of connections and open new connections if needed by clients.

Let's try again and notice how our Database object is transformed as we open a pool:

   .. code-block:: python

        # Initialize database
        database = jumbo.database.Database(jumbo.config.Config())

        loguru.logger.info(f"Before opening the pool the 'pool' is:{database.pool}")

        # Create a connection pool with two connections.
        with database.open(minconns=2, maxconns=4) as pool:

            loguru.logger.info(f"After opening the pool the 'pool' is:{pool.pool}")

        loguru.logger.info(f"After closing the pool the 'pool' is:{database.pool}")

Connecting to the Database
--------------------------

We are now all set to use a connection from the pool to send queries to the PostgreSQL database. We do this in jumbo via the Database.connect() method, which also supports a context-manager syntax to make sure that connections are properly taken from the pool and correctly put back in the pool at the end of a client's transactions:

    .. code-block:: python

        # Initialize database
        database = jumbo.database.Database(jumbo.config.Config())

        # Create a connection pool
        with database.open() as pool:

            # Get individual connection from the pool. Context manager ensures connection is returned to the pool.
            with pool.connect():

                pass

Here we have create out Database object, opened a connection pool offering a single connection, and finally connected to the database with that connnection. By default our client sends a 'SELECT version()' SQL command to the database, hence why we receive a response back from the server.

The double context-manager construct used in jumbo may seem a bit cumbersome at first, but it is one of the key strengths of jumbo as it allows to automatically take care of all SQL connection protocols behind the scenes, and ensures proper garbage collection of transactions and connections for all clients.

Once more the following example will let you have a look at how our Database object is transformed as we open pools and actuate connections:

    .. code-block:: python


        # Initialize database
        database = jumbo.database.Database(jumbo.config.Config())

        loguru.logger.info(f"Before opening the pool:{database.pool}")

        # Create a connection pool with two connections. Context manager ensures pool
        with database.open() as pool:

            loguru.logger.info(f"After opening the pool: {pool.pool}")

            with pool.connect():

                loguru.logger.info(f"After connecting:{pool.pool}")

                pass

            loguru.logger.info(f"After disconnecting:{pool.pool}")

        loguru.logger.info(f"After closing the pool:{database.pool}")

**Note:** As a very last point, you should be assigning keys to identify connections taken from the pool. In this way it is easy to keep track of which connection is being used to send queries to the database. In the cells before we took advantage of the implicit key=1 keyword argument used by Database.connect().

To summarize, a proper jumbo hello-world script looks like the following:

    .. code-block:: python

        import jumbo

        if __name__ == "__main__":

            # Initialize database object
            database = jumbo.database.Database(jumbo.config.Config())

            # Create a connection pool. Context manager ensures pool is closed at the end.
            with database.open(minconns=1) as pool:

                # Get individual connection from the pool. Context manager ensures connection [key] is returned to the pool at the end.
                with pool.connect(key=1):

                    pass  # do wahtever you want here!

It's your turn now! Experiment with what you have lernt so far.

E.g. try firing several connections, then try firing more connections that your pool can handle!


=====================
Database Interactions
=====================

In this tutorial you will learn how to send SQL queries with jumbo.

First things first:

- make sure you have a PostgreSQL server available, and a user account to connect to it.
- make sure you have a properly configured jumbo.env file in the root directory of this notebook

   .. code-block::

         DATABASE_HOST = <my_database_host_address>
         DATABASE_USERNAME = <my_database_user_name>
         DATABASE_PASSWORD = <my_database_user_password>
         DATABASE_PORT = <my_database_port>
         DATABASE_NAME = <my_database_name>

- make sure your user account has appropriate permissions on the database tables you will access

At this point we can start using the library:

   .. code-block:: python

        import jumbo

And start with our minimal example:

   .. code-block:: python

        # Initialize database object
        database = jumbo.database.Database(jumbo.config.Config())

        # Create a connection pool. Context manager ensures pool is closed at the end.
        with database.open() as pool:

            # Get individual connection from the pool. Context manager ensures connection [key] is returned to the pool at the end.
            with pool.connect():

                pass  # do whatever you want here!

Except for the implicit handshake between our client and the database happening behind the scene and retrieving the databases version, we still haven't done anything with the connection we have fished out from the pool... Let's now see how to send our own SQL queries to the database.

You will need some minimal SQL knowledge to follow the following tutorial, but you can easily recycle code and get help online.

Creating a table
----------------

You are now connected to a database but there might not be any tables there to hold data. Let's now create a table called *data_container* with the columns of our choice. Here we decide on four columns called *unix_timestamp*, *iso_timestamp*, *device*, and *reading*. The SQL query to create such a table is the following:

   .. code-block:: postgresql

        CREATE TABLE IF NOT EXISTS data_container
        (unix_timestamp FLOAT PRIMARY KEY NOT NULL,
        iso_timestamp TIMESTAMP,
        device varchar(255),
        reading INT);


Note that we need to specify the (PostgreSQL) type of values that we will populate the columns with, and optionally which column to use as the PRIMARY KEY. This column should only contain unique and non-null values.

To create such a table in jumbo we would do it this way:

   .. code-block:: python

        # SQL query to create a table; remember to specify primary key column
        SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS data_container \
                            (unix_timestamp FLOAT PRIMARY KEY NOT NULL,' \
                            'iso_timestamp TIMESTAMP,' \
                            'device varchar(255),' \
                            'value INT);'


        # Initialize database object
        database = jumbo.database.Database(jumbo.config.Config())

        # Create a connection pool.
        with database.open() as pool:

            # Get individual connection from the pool.
            with pool.connect(key=1):

                # send a 'CREATE TABLE' SQL query using connection [1] from the pool
                pool.send(SQL_CREATE_TABLE, key=1)

If everything went well you should see a 'Table created successfully' log. You have just successfully executed your first SQL query with jumbo!

Inserting Data in a table
-----------------------------

Now that we have a table, it's time to upload some data. The SQL query to insert a data row in our table is the following:

   .. code-block:: postgresql

        INSERT INTO data_container (unix_timestamp, iso_timestamp, device, value)
        VALUES (1000.1, "2020-03-26 10:26:08.450800", "DataLogger X1", 23);


where we have just listed again the table name, and column names of the table we want to write into, and then passed compatible values for each field.

To execute this command in jumbo we naturally do it as follows:

   .. code-block:: python

        # SQL query to create a table; remember to specify primary key column
        SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS data_container \
                            (unix_timestamp FLOAT PRIMARY KEY NOT NULL,' \
                            'iso_timestamp TIMESTAMP,' \
                            'device varchar(255),' \
                            'value INT);'

        # Create a Template SQL command to inject table with entries; %s will be replaced with values later
        SQL_INSERT_IN_TABLE = 'INSERT INTO data_container ' \
                              '(unix_timestamp, iso_timestamp, device, value) ' \
                              'VALUES (%s, %s, %s, %s);'

        # Initialize database object
        database = jumbo.database.Database(jumbo.config.Config())

        # Create a connection pool. Context manager ensures pool is closed at the end.
        with database.open() as pool:

            # Get individual connection from the pool.
            with pool.connect(key=1):

                # create table to hold the data
                pool.create_table(SQL_CREATE_TABLE, key=1)

                # Now let's imagine we now suddenly get values to insert in the table
                timestamp_now = datetime.datetime.timestamp(datetime.now())
                timestamp_now_iso = datetime.datetime.fromtimestamp(timestamp_now).isoformat()
                value = 23

                # Collect in a tuple
                substitutions = (timestamp_now, timestamp_now_iso, "DataLogger X1", value)
                # Insert data
                pool.send(SQL_INSERT_IN_TABLE, substitutions, key=1)


If everything went smoothly you should see a 'Record inserted successfully' log. Note that here we have exploited the ability of defining a generic INSERT query, with specific values only substituted in dynamically later on. In this way we can create a single INSERT query for a given table and use it for any kind of data we might be generating later.

**Important:** your 'substitutions' should always be a tuple. Hence if your had a template like this:

   .. code-block:: postgresql

        INSERT INTO table_name (column_name)
        VALUES (%s);

You should then be passing 'substitutions' looking like this:

   .. code-block:: python

        substitutions = (value,)

**Also Important:** this %s formatting is a completely independent thing of python's %-formatting string substitutions. So don't confuse the two. This %s construct is proper to psycopg2, the PostgreSQL library on which jumbo is based. For more informmation feel free to visit https://www.psycopg.org/docs/usage.html

Also, as said by psycopg2: never, never, NEVER use Python string concatenation (+) or string parameters interpolation (%) to pass variables to a SQL query string. Not even at gunpoint.

Just use the jumbo interface, as explained above and everything is taken care of automatically!

Pulling Data from the Database
------------------------------

We now have a table populated with some data. It's time to see how to fetch that data back from the database.

The SQL query to select all data from a table is as follows:

   .. code-block:: postgresql

        SELECT * from table_name;

Hence in jumbo we would do this:

   .. code-block:: python

        # SQL query to create a table; remember to specify primary key column
        SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS data_container \
                            (unix_timestamp FLOAT PRIMARY KEY NOT NULL,' \
                            'iso_timestamp TIMESTAMP,' \
                            'device varchar(255),' \
                            'value INT);'

        # Create a Template SQL command to inject table with entries; %s will be replaced with values later
        SQL_INSERT_IN_TABLE = 'INSERT INTO data_container ' \
                              '(unix_timestamp, iso_timestamp, device, value) ' \
                              'VALUES (%s, %s, %s, %s);'

        # SQL query to pull all data from the table
        SQL_SELECT = 'SELECT * FROM data_container'

        # Initialize database object
        database = jumbo.database.Database(jumbo.config.Config())

        # Create a connection pool
        with database.open() as pool:

            # Get individual connection from the pool
            with pool.connect(key=1):

                # create table to hold the data
                pool.create_table(SQL_CREATE_TABLE, key=1)

                # Now let's imagine we suddenly get values to insert in the table
                timestamp_now = ddatetime.datetime.timestamp(datetime.now())
                timestamp_now_iso = datetime.datetime.fromtimestamp(timestamp_now).isoformat()
                value = 23

                # Collect in a tuple
                substitutions = (timestamp_now, timestamp_now_iso, "DataLogger X1", value)
                # Insert data
                pool.send(SQL_INSERT_IN_TABLE, substitutions, key=1)

                # Let's wait a few seconds ...
                time.sleep(2)

                # Now we want to get back data from our table
                results = pool.send(SQL_SELECT, key=1)

                # Results will hold a list of all rows returned by our query
                loguru.logger.info(results)

                # These are dictionary-like object whose values can be accessed by column name
                for row in results:
                    loguru.logger.info(row['unix_timestamp'])

Perfect we have finished our little tour of basic SQL interactions from the database! You should now know how to create tables, upload, and retrieve data!

As you have seen, jumbo allows to send arbitrary SQL queries through the Database.send() method. Don't hesitate to browse the documentation to checkout all keyword parameters that can be used with Database.send()!

Let's see one last example in action. In the following example we clean up our database by removing the table we have created above:

   .. code-block:: python

        # Initialize database object
        database = jumbo.database.Database(jumbo.config.Config())

        # Create a connection pool. Context manager ensures pool is closed at the end.
        with database.open() as pool:

            # Get individual connection from the pool. Context manager ensures connection [key] is returned to the pool at the end.
            with pool.connect(key=1):

                # Our generic SQL query
                SQL_DROP = 'DROP TABLE IF EXISTS data_container'

                # Execute query
                pool.send(SQL_DROP, key=1)

More user friendly queries
--------------------------

If you are not an SQL expert it might be a little daunting to handle data through raw SQL queries - don't worry! Jumbo is here to the rescue with plenty of functionalities to make data processing easier!

For example jumbo offers functions such as

   .. code-block:: python

        jumbo.utils.convert_to_df(query_results)

which allows to convert SQL query results directly to a pandas.DataFrame - which you might be much more familiar with to parse/filter/group_by etc...

In this way you can issue a generic and easy to remember

   .. code-block:: python

        results = Database.send('SELECT * FROM table_name')


and then convert immediately the query results into a dataframe, on which to perform all the data anlysis that you like!

   .. code-block:: python

        df = jumbo.utils.convert_to_df(results)


Let's now say you would like to upload the results of your data analysis back in a table on the database. If you followed the notebook above you might be a bit scared of having to write a CREATE TABLE query with correct column names / column types and then having to perform INSERT statements with %s substitutions all over the place...

Luckily with jumbo you can just do everything in one line:

   .. code-block:: python

        Database.copy_df(df, new_table_name)

What a treat!

Don't hesitate to look at the other notebooks for more inspiration on how to implement all of this in practice!

====================
Filesystem Watchdogs
====================

In this tutorial you will learn how to use jumbo's watchdog functionalities. By the end you will have created a simple watchdog looking for any new data being written in a directory and uploading it automatically to a database table.

First things first:

- make sure you have a PostgreSQL server available, and a user account to connect to it.
- make sure you have a properly configured jumbo.env file in the root directory of this notebook

   .. code-block::

         DATABASE_HOST = <my_database_host_address>
         DATABASE_USERNAME = <my_database_user_name>
         DATABASE_PASSWORD = <my_database_user_password>
         DATABASE_PORT = <my_database_port>
         DATABASE_NAME = <my_database_name>

- make sure your user account has appropriate permissions on the database tables you will access

If you are deploying jumbo in practical applications, you might be interested in deploying a watchdog to automatically stream new data to a table in your database. Ideally you would interface directly with the data generator and INSERT each new data entry to the table, but this is not always possible. Data acquisition from the data generator might be blocked by proprietary software, or for legacy reasons you cannot interfere directly with the data collection protocol already in place. In this cases the only thing left to do might be to monitor the output files where data is being saved to and upload any change to the database.

Watchdogs
-----------

Let's setup everything to simulate our working environment. We need two things:

- A bot script writing data to files, to simulate a real data generator
- Our watchdog deployed to monitor those files

Let's start by setting-up a very simple monkey-writer. The following code does nothing special, it will simply write the current timestamp to a file called *fake_data.txt* in the *data* directory. Each write will happen after a random time interval. Run the following code to get a feeling of how it works and then STOP IT before moving to the next section.

   .. code-block:: python

        # Monkey Writer

        import time
        import loguru
        import numpy

        try:

            while True:

                # Need to open/close file on every write so that watchdog can see each change
                with open('data/fake_data.txt', "a") as f:

                    # Write current timestamp
                    number = time.time()
                    f.write(str(number) + '\n')
                    loguru.logger.debug(f"Wrote number {number} to file")

                # Wait a variable amount of time before writing next
                time.sleep(numpy.random.randint(10))

        except KeyboardInterrupt:
            loguru.logger.error("Monkey writer has been stopped via Keyboard Interrupt.")


Now that we have a data source let's deploy a watchdog on the *data* folder.

Jumbo let's you create watchdogs very easily. Here is  jumbo's implementation of a watchdog:

   .. code-block:: python

        import jumbo

        # Initialize database
        database = jumbo.database.Database(jumbo.config.Config())

        # Create a connection pool
        with database.open() as pool:

            # Get individual connections from the pool
            with pool.connect(key=1):

                # Initialize the table to hold watched data
                SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS data_container (ID FLOAT PRIMARY KEY NOT NULL);'
                pool.send(SQL_CREATE_TABLE, key=1)

                # Template SQL command to inject table with entries from file
                SQL_INSERT_IN_TABLE = "INSERT INTO data_container (ID) VALUES (%s)"  # %s will be replaced with .txt line fields

                # Create watchdog
                fido = jumbo.handlers.FileWatcher(pool, SQL_INSERT_IN_TABLE, 'data/', timeout=0.5, key=1)

                # Deploy watchdog
                fido.bark()

Let's have a look at what is going on in the code:

As we have seen before we start by creating a database object, opening a connection pool, and setting  up a connection to the PostgreSQL database. We then create a table on the database to hold the data we will collecting from the files, and prepare an INSERT statement to dynamically insert the values collected from the files into the table.

We then create a jumbo handlers.FileWatcher watchdog

    .. code-block:: python

        jumbo.handlers.FileWatcher(pool, SQL_INSERT_IN_TABLE, 'data/', timeout=0.5, key=1)


This watchdog looks for changes in .txt files in the *data* folder by polling for changes every 0.5s. It then executes the query template of our choice with every new entry added to the files passed dynamically. That is everytime a change is detected the watchdog will implicitely perform a

    .. code-block:: postgresql

        INSERT INTO data_container (ID) new_value;

Finally we deploy the watchdog via the .bark() method. This activates the watchdog and schedules it's handler to fire on each 'file modified event' detected.

Don't hesitate to have a look at the documentation to look at all the customisable parameters. Or have a look at the source code to implement your own tailored watchdogs! You can implement your own watchdogs and event handlers!

Now run both code scripts above at the same time and see if the behaviour in the logs makes sense!