# 🎈 Basic Usage

You will find here a collection of detailed code examples guiding you through core jumbo features. If it's your first
time using jumbo, you are strongly suggested to follow the tutorials in order. If you are an experienced jumbo user feel
free to skip to the section you need a refresher on. These tutorials are an excellent introduction to the library and
will help build familiarity with its syntax and usage protocols.

(basic/setup)=
````{note}
Before running any jumbo script always make sure you have the following
 configured:

1. A PostgreSQL server up and running

2. A user account enabled on the server, with appropriate permissions

3. A `jumbo.env` configuration file on your local machine:

   >```
   >DATABASE_HOST = <my_database_host_address>
   >DATABASE_USERNAME = <my_database_user_name>
   >DATABASE_PASSWORD = <my_database_user_password>
   >DATABASE_PORT = <my_database_port>
   >DATABASE_NAME = <my_database_name>
   >```

Don't hesitate to refer to [First Step](intro_package.md) and 
[Database Setup](intro_database.md) for more details!
````

```{tip}
To follow along with the tutorials, [tweak the logger](documentation.md) shipped with jumbo!
```


(basic/hello-world)=
## 🌈 Hello World

In this tutorial you will build jumbo's `Hello World!` from the ground up, and
 learn a few things about how it works behind the scenes. Let's dive
  straight in!

```{tip}
Make sure your jumbo environment is [setup as expected](intro_package.md)!
```

To start using the library, simply import it as follows:

```python
import jumbo
```

### Jumbo's `Database` Object

One of the most important objects in the jumbo library is the `Database` object
(`jumbo.database.Database`). This `Database` object is jumbo's representation 
of the PostgreSQL database we want to connect to. The `Database` allows to
create connections to the real PostgreSQL server and will automatically
manage all transactions with it. Creating a `Database` is extremely simple:

```python
import jumbo

database = jumbo.database.Database()
```

Behind the scenes, jumbo looks for our `jumbo.env` configuration file -
storing all of the parameters needed to connect to the PostgreSQL database.
        
To double check whether the `Database` connection manager has loaded the
correct configuration settings you can peek into its `Config` container
(`jumbo.config.Config`). Let's have a look:

```python
import jumbo

database = jumbo.database.Database()

print(database.config)
```
```
>>>

DATABASE CONFIGURATION SETTINGS:
ENV_PATH:	path\to\jumbo.env
DATABASE_HOST:	host_address
DATABASE_PORT:	5432
DATABASE_NAME:	database_name
DATABASE_PASSWORD:	xxx
DATABASE_USERNAME:	database_username
```

Conveniently, these configuration settings are also logged out automatically 
by jumbo on creation of the `Database`. To display these logs you just need
to decrease the threshold of the default [jumbo loggers](documentation.md) to 
`INFO` level.

````{tip}
You can also choose to have your `jumbo.env` file in a single private location
, instead of always placing a copy in your
current working directory. In that case pass the path to the directory
 containing your `jumbo.env` file on construction of the
`Database` object:

   ```python
   import python

   # jumbo.env is in 'secret' directory
   my_env_path = "D:\\dumbo\\secret"

   database = jumbo.database.Database(my_env_path)
   ```
````

### Connection Pools


At this point we would like to connect to the database. In general, opening 
and closing multiple connections to a database creates a bit of overhead - 
it's more efficient to first initialize a so called connection-pool of $n$ 
connections from which clients can take and put back individual connections
as they need them. In jumbo we do this in this way:

```python
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)  
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# Initialize database
database = jumbo.database.Database()

# Create a connection pool. Context manager ensures pool is closed at the end.
with database.open() as pool:

    logger.info("Opened a connection pool.")

    logger.debug(pool.pool)
```
The context-manager structure ensures behind the scenes that the connection 
pool is opened correctly and closed successfully at the end of the script.

Note that in the above example we opened a connection pool containing by
default a single connection, but we can open pools with a minimum and 
maximum number of available connections using the `minconns` and `maxconns` 
arguments. The pool will initialize with a minimum amount of connections and
make available new connections if needed by clients.

Let's try again and notice how our `Database` connection manager gets
updated as we open a pool:

```python
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)  
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# Initialize database
database = jumbo.database.Database()

logger.info(f"Before opening the pool the 'pool' is:{database.pool}")

# Create a connection pool with two connections.
with database.open(minconns=2, maxconns=4) as pool:

    logger.info(f"After opening the pool the 'pool' is:{pool.pool}")

logger.info(f"After closing the pool the 'pool' is:{database.pool}")
```

All good so far - but as you can see from the logs generated above - we are
still simply opening and closing the connection pool. None of the
connections made available through the pool are actually being used to
 connect to the database. If in doubt, don't hesitate to double check the
  status of the pool and its connections through the `pool` attribute of the
   `Database` connection manager.


### Connecting to the Database


We are now all set to use a connection from the pool to send queries to the 
PostgreSQL database. We do this in jumbo via the `connect()` method of our
 `Database` connection manager, which also supports a context-manager syntax 
 to make sure that connections are properly taken from put back in the pool at 
 the end of a client's transactions:

```python
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# Initialize database
database = jumbo.database.Database()

# Create a connection pool
with database.open() as pool:

    # Get individual connection from the pool. 
    # Context manager ensures connection is returned to the pool.
    with pool.connect():

        pass
```

Here we have created our `Database` object, opened a connection pool offering a 
single connection, and finally connected to the database with that connnection. 
By default our client sends a handshake `SELECT version()` SQL
 command to the database, hence why we receive a response back from the server.

The double context-manager construct used in jumbo may seem a bit cumbersome 
at first, but it is one of the key strengths of jumbo as it allows to 
automatically take care of all SQL connection protocols behind the scenes, 
and ensures proper garbage collection of transactions and connections for all 
clients.

Once more the following example will let you have a look at how our `Database`
connection manager transforms as we open pools and actuate connections:

```python
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# Initialize database
database = jumbo.database.Database()

logger.info(f"Before opening the pool:{database.pool}")

# Create a connection pool with two connections. Context manager ensures pool
with database.open() as pool:

    logger.info(f"After opening the pool: {pool.pool}")

    with pool.connect():

        logger.info(f"After connecting:{pool.pool}")

        pass

    logger.info(f"After disconnecting:{pool.pool}")

logger.info(f"After closing the pool:{database.pool}")
```

```{note}
As a very last point, you should be assigning keys to identify connections
taken from the pool. In this way you can keep track of which connection 
is being used to send which queries to the database. In the cells before we
took advantage of the implicit `key=1` keyword argument used by `connect()`.
```

To summarize, here is our final jumbo hello-world script:

```python

import jumbo

if __name__ == "__main__":

    # Initialize database object
    database = jumbo.database.Database()

    # Create a connection pool. 
    # Context manager ensures pool is closed at the end.
    with database.open(minconns=1) as pool:

        # Get individual connection from the pool. 
        # Context manager ensures connection [key] is returned to the pool.
        with pool.connect(key=1):

            pass  # do whatever you want here!
```

It's your turn now! Experiment with what you have learnt so far.

E.g. try firing several connections, then try firing more connections that 
your pool can handle!


## 📤 Database Interactions


In this tutorial you will learn how to send SQL queries with jumbo.

```{tip}
Make sure your jumbo environment is [setup as expected](intro_package.md)!
```

Let's start with jumbo's `Hello World`:

```python
import jumbo

# Initialize database object
database = jumbo.database.Database()

# Create a connection pool. Context manager ensures pool is closed at the end.
with database.open() as pool:

    # Get individual connection from the pool. 
    # Context manager ensures connection [key] is returned to the pool.
    with pool.connect():

        pass  # do whatever you want here!
```

Except for the implicit handshake between our client and the database 
happening behind the scene and retrieving the databases version, we still 
haven't done anything with the connection we have fished out from the pool... 
Let's now see how to send our own SQL queries to the database.

```{note}
You will need some minimal SQL knowledge to follow the following tutorial, 
but you can easily recycle code form here and get help online.
```

### Creating a table

You are now connected to a database, which may or may not have tables setup
to hold data. Let's create our own table called `my_table` with the columns
 of our choice. Here we decide on four columns called `unix_timestamp`, 
 `iso_timestamp`, `device`, and `reading`. The SQL query to create such a
  table is the following:

```sql
CREATE TABLE IF NOT EXISTS my_table
(unix_timestamp FLOAT PRIMARY KEY NOT NULL,
iso_timestamp TIMESTAMP,
device varchar(255),
reading INT);
```

Note that we need to specify the (PostgreSQL) type of the values that we will
 populate the columns with, and optionally which column to use as the 
 `PRIMARY KEY`. This column should only contain unique and non-null values.

To create such a table in jumbo we just send our pre-formatted SQL query to
 the database as follows:

```python
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# SQL query to create a table; remember to specify primary key column
SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS my_table ' \
                   '(unix_timestamp FLOAT PRIMARY KEY NOT NULL,' \
                   'iso_timestamp TIMESTAMP,' \
                   'device varchar(255),' \
                   'value INT);'

# Initialize database object
database = jumbo.database.Database()

# Create a connection pool.
with database.open() as pool:

    # Get individual connection from the pool.
    with pool.connect(key=1):

        # send a 'CREATE TABLE' SQL query using connection [1] from the pool
        pool.send(SQL_CREATE_TABLE, key=1)
```

If everything went well you should get echoed back a log like the following:

```bash
INFO | Successfully sent: b'CREATE TABLE IF NOT EXISTS my_table (unix_timestamp FLOAT PRIMARY KEY NOT N'... 
```

That's it! You've done it! You have just successfully executed your first SQL 
query with jumbo! 🎉

### Inserting Data in a table


Now that we have a table, it's time to upload some data. The SQL query to 
insert a new sample row in our table is the following:

```sql
INSERT INTO my_table (unix_timestamp, iso_timestamp, device, value)
VALUES (1000.1, '2020-03-26 10:26:08.450800', 'DataLogger X1', 23);
```

where we have just listed again the table name, and column names of the table 
we want to write to, and then passed compatible values for each field.

To execute this command in jumbo we naturally do it as follows:

```python
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# SQL query to create a table; remember to specify primary key column
SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS my_table ' \
                   '(unix_timestamp FLOAT PRIMARY KEY NOT NULL,' \
                   'iso_timestamp TIMESTAMP,' \
                   'device varchar(255),' \
                   'value INT);'

# Create a Template SQL command to inject table with entries;
SQL_INSERT_IN_TABLE = "INSERT INTO my_table " \
                      "(unix_timestamp, iso_timestamp, device, value) " \
                      "VALUES (1000.1, '2020-03-26 10:26:08.450800', 'DataLogger X1', 23);"

# Initialize database object
database = jumbo.database.Database()

# Create a connection pool. Context manager ensures pool is closed at the end.
with database.open() as pool:

    # Get individual connection from the pool.
    with pool.connect(key=1):

        # create table to hold the data (if it doesn't already exist)
        pool.send(SQL_CREATE_TABLE, key=1)

        # Insert data
        pool.send(SQL_INSERT_IN_TABLE, key=1)
```

If everything went smoothly you should see echoed back the following log:

```bash
Successfully sent: b'INSERT INTO my_table (unix_timestamp, iso_timestamp, device, value) VALUES '...
```

#### Inserting data with substitutions

If you were to have to prepare a new SQL string everytime you wanted to send
 different data to a database table it would get cumbersome very quickly
 ... luckily jumbo allows you to create a template SQL query which gets
  filled dynamically with new data once it's time to upload it. Let's see
   how it works:
 
```python
import jumbo
import logging
import datetime

# Setup your basic logger
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s | %(message)s',
    datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# SQL query to create a table; remember to specify primary key column
SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS my_table ' \
                   '(unix_timestamp FLOAT PRIMARY KEY NOT NULL,' \
                   'iso_timestamp TIMESTAMP,' \
                   'device varchar(255),' \
                   'value INT);'

# Create a Template SQL command to inject table with entries;
# %s will be replaced with values later
SQL_INSERT_IN_TABLE = 'INSERT INTO my_table ' \
                      '(unix_timestamp, iso_timestamp, device, value) ' \
                      'VALUES (%s, %s, %s, %s);'

# Initialize database object
database = jumbo.database.Database()

# Create a connection pool. Context manager ensures pool is closed at the end.
with database.open() as pool:
    # Get individual connection from the pool.
    with pool.connect(key=1):
        # create table to hold the data
        pool.send(SQL_CREATE_TABLE, key=1)

        # Now let's imagine we now suddenly get values to insert in the table
        timestamp_now = datetime.datetime.timestamp(datetime.datetime.now())
        timestamp_now_iso = datetime.datetime.fromtimestamp(timestamp_now).isoformat()
        value = 23

        # Collect in a tuple
        substitutions = (timestamp_now, timestamp_now_iso, "DataLogger X1", value)

        # Insert data
        pool.send(SQL_INSERT_IN_TABLE, subs=substitutions, key=1)
```

Here we have exploited the ability of defining a generic `INSERT` query, with
 specific values only substituted in dynamically later on. In this way we can 
 create a single `INSERT` query for a given table and use it for any kind of 
 data we might be generating later.

````{warning}
Your `subs` should always be formatted as a tuple. Hence if your had to fill a
 SQL template like this:

   ```sql
   INSERT INTO table_name (column_name)
   VALUES (%s);
   ```

You should still be passing substitutions to `send()` as a tuple, like this:

   ```python
   subs = (value,)
   ```
````

```{warning}
The `%s` formatting we are using in our SQL templates is completely
 independent from python's *old-style* string formatting (% operator). 
So don't confuse the two. This `%s` construct is proper to `psycopg2`, 
the PostgreSQL library on which jumbo is based. For more informmation feel 
free to visit its [official documentation](https://www.psycopg.org/docs/usage.html)

Also, as said by `psycopg2` 

>never, **never**, **NEVER** use Python string concatenation (+) or string
> parameters interpolation (%) to pass variables to a SQL query string. Not
> even at gunpoint.

Just use the jumbo interface as explained above and everything will be taken
 care of automatically!
```

### Pulling Data from the Database


We now have a table populated with some data. It's time to see how to fetch 
that data back from the database.

The SQL query to select all data from a table is as follows:

```sql
SELECT * from table_name;
```     

Hence in jumbo we would do this:

```python
import time
import jumbo
import logging
import datetime

# Setup your basic logger
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s | %(message)s',
    datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# SQL query to create a table; remember to specify primary key column
SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS my_table ' \
                   '(unix_timestamp FLOAT PRIMARY KEY NOT NULL,' \
                   'iso_timestamp TIMESTAMP,' \
                   'device varchar(255),' \
                   'value INT);'

# Create a Template SQL command to inject table with entries;
# %s will be replaced with values later
SQL_INSERT_IN_TABLE = 'INSERT INTO my_table ' \
                      '(unix_timestamp, iso_timestamp, device, value) ' \
                      'VALUES (%s, %s, %s, %s);'

# SQL query to pull all data from the table
SQL_SELECT = 'SELECT * FROM my_table'

# Initialize database object
database = jumbo.database.Database()

# Create a connection pool
with database.open() as pool:

    # Get individual connection from the pool
    with pool.connect(key=1):

        # create table to hold the data
        pool.send(SQL_CREATE_TABLE, key=1)

        # Now let's imagine we suddenly get values to insert in the table
        timestamp_now = datetime.datetime.timestamp(datetime.datetime.now())
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
        logger.info(results)

        # These are dictionary-like object whose values can be accessed by column name
        for row in results:
            logger.info(f"Time {row['unix_timestamp']}: value {row['value']}")
```

### Dropping data from the database

Let's see one last example in action. In the following example we clean up our 
database by removing the table we have created above. The SQL command to do
 this is as follows:

```sql
DROP TABLE IF EXISTS table_name
```

So in jumbo we just need to do this:

```python
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s | %(message)s',
    datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# Initialize database object
database = jumbo.database.Database()

# Create a connection pool. Context manager ensures pool is closed at the end.
with database.open() as pool:

    # Get individual connection from the pool. 
    # Context manager ensures connection [key] is returned to the pool.
    with pool.connect(key=1):

        # Our generic SQL query
        SQL_DROP = 'DROP TABLE IF EXISTS my_table'

        # Execute query
        pool.send(SQL_DROP, key=1)
```

Perfect we have finished our little tour of basic SQL interactions from the 
database! You should now know how to create tables, upload, and retrieve data!
🎉

As you have seen, jumbo allows to send arbitrary SQL queries through the
 `send()` method. Don't hesitate to browse the documentation to checkout all 
 keyword parameters that can be used with `send()`!
 

### More user friendly queries

If you are not familiar with SQL, it might be a little daunting to handle data
 through raw SQL queries - don't worry! Jumbo is here to the rescue with 
 plenty of functionalities to make data processing easier!

For example jumbo offers functions such as

```python
jumbo.utils.convert_to_df(query_results)
```

which allows to convert SQL query results directly to a `pandas.DataFrame` - 
which you might be much more familiar with to parse/filter/group_by etc...

In this way you can issue a generic and easy to remember

```
results = pool.send('SELECT * FROM table_name')
```

and then convert immediately the query results into a dataframe, 
on which to perform all the data anlysis that you like!

```python
df = jumbo.utils.convert_to_df(results)
```

Let's now say you would like to upload the results of your data analysis 
back in a table on the database. If you followed this tutorial all along
 you might be a bit scared of having to write a `CREATE TABLE ...` query with
  correct column names / column types and then having to perform `INSERT`
  statements with `%s` substitutions all over the place...

Luckily with jumbo you can just do everything in one line:

```
pool.copy_df(df, new_table_name)
```

What a treat! 😇 🎉