# 🐶 Filesystem Watchdogs

In this tutorial you will learn how to use jumbo's watchdog functionalities
. By the end you will have created a simple watchdog looking for any new
 data being written in a directory and uploading it automatically to a database table.

```{tip}
Make sure your jumbo environment is [setup as expected](intro_package.md)!
```

If you are deploying jumbo in practical applications, you might be
 interested in deploying a watchdog to automatically stream new data to a
  table in your database. Ideally you would interface directly with the data
   generator and `INSERT` each new data entry to the table, but this is not
    always possible. Data acquisition from the data generator might be
     blocked by proprietary software, or for legacy reasons you cannot
      interfere directly with the data collection protocol already in place
      . In this cases the only thing left to do might be to monitor the
       output files where data is being saved to and upload any change to
        the database.... This is where a filesystem watchdog comes to the
         rescue!

Let's setup everything to simulate our working environment. We need two things:

- A bot script writing data to files, to simulate a real data generator
- Our watchdog deployed to monitor those files

Let's start by setting-up a very simple data generator. The following code does
 nothing special, it will simply write the current timestamp to a file
  called `fake_data.txt` in the `data/` directory. Each write will happen
   after a random time interval. Run the following code to get a feeling of
    how it works and then *STOP IT* before moving to the next section.

```python
# data_generator.py
import time
import logging
import pathlib
import numpy

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

try:

    pathlib.Path('data/').mkdir(parents=True, exist_ok=True)

    while True:

        # Need to open/close file on every write so that watchdog can see each
        # change
        with open('data/fake_data.txt', "a") as f:

            # Write current timestamp
            number = time.time()
            f.write(str(number) + '\n')
            logger.debug(f"Wrote number {number} to file")

        # Wait a variable amount of time before writing next
        time.sleep(numpy.random.randint(5))

except KeyboardInterrupt:
    logger.warning("Data generator has been stopped via Keyboard Interrupt.")
```

Now that we have a data source let's deploy a watchdog on the `data` folder.

Jumbo let's you create watchdogs very easily. Here is  jumbo's
 implementation of a watchdog:

```python
#watchdog.py
import jumbo
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

# lower the severity level of jumbo logs being displayed
logging.getLogger('jumbo').setLevel("INFO")

# Initialize database
database = jumbo.database.Database()

# Create a connection pool
with database.open() as pool:

    # Get individual connections from the pool
    with pool.connect(key=1):

        # Initialize the table to hold watched data
        SQL_CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS my_table ' \
                           '(ID FLOAT PRIMARY KEY NOT NULL);'
        pool.send(SQL_CREATE_TABLE, key=1)

        # Template SQL command to inject table with entries from file
        # %s will be replaced with .txt line fields
        SQL_INSERT_IN_TABLE = "INSERT INTO data_container (ID) VALUES (%s)"

        # Create watchdog
        fido = jumbo.handlers.FileWatcher(pool, SQL_INSERT_IN_TABLE, 
                                          src_path='data/', 
                                          timeout=0.5, key=1)

        # Deploy watchdog
        fido.bark()
```

Let's have a look at what is going on in the code...

As usual, we start by creating a database object, opening a
 connection pool, and setting  up a connection to the PostgreSQL database
 . We then create a table (`my_table`) on the database to hold the data we will
  collecting from the files, and prepare an `INSERT` statement to
   dynamically insert the values collected from the files into the table.

We then create a `jumbo handlers.FileWatcher()` watchdog:

```python
jumbo.handlers.FileWatcher(pool, 
                           query=SQL_INSERT_IN_TABLE, 
                           src_path='data/', 
                           timeout=0.5)
```

This watchdog looks for changes in `.txt` files in the `data/` folder by
 polling for changes every `timeout` seconds. It then executes the `query` SQL
  template of our choice with every new entry added to the files passed 
  dynamically. That is, everytime a change is detected the watchdog will
   implicitly perform a:

```sql
INSERT INTO my_table (ID) new_value;
```

Finally we deploy the watchdog via the `.bark()` method. This activates the
 watchdog and schedules it's handler to fire on each **file modified event** detected.

Don't hesitate to have a look at the documentation to look at all the
 customisable parameters. Or have a look at the source code to implement
  your own tailored watchdogs! You can implement your own watchdogs and
   event handlers!

Now run both code scripts above at the same time and see if the behaviour in
 the logs makes sense!