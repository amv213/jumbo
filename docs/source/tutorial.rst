.. _tutorial:

***********
First steps
***********

Welcome to jumbo! The PostgreSQL library for scientist.

Jumbo is a wrapper of psycopg2 - the most popular PostgreSQL database adapter for the Python programming language. Jumbo
has been designed specifically for adoption in scientific research environments, where thorough widespread knowledge of
SQL protocols might be lacking and a streamlined approach to database interactions might be needed. Jumbo offers an
intuitive and quickly deployable interface to successfully implement a database-centred data analysis pipeline at all
levels of the organisation. Jumbo is intuitive yet customizable - first-time users can easily interact with the database
without worrying about handling transactions under the hood, while experienced PostgreSQL architects can unleash the
full power of jumbo to exploit advanced PostgreSQL functionalities.

============
Installation
============

You can install jumbo like any other Python package, using pip to download it from PyPI:

    .. code-block:: python

        pip install jumbo==0.0.2b

or using setup.py if you have downloaded the source package locally:

    .. code-block:: python

        python setup.py build
        sudo python setup.py install

You can also install the latest development of jumbo from testPyPI:

    .. code-block:: python

        pip install -i https://test.pypi.org/simple/ jumbo==0.0.2b0


=========================
Configuring your database
=========================

To start using jumbo you need to have a PostgreSQL database to connect to. This can be running on your local machine or
anywhere on your network. You also need to have setup a PostgreSQL user account with appropriate privileges to access
that database. If you are unsure about what any of the previous sentence actually means get in touch with your
PostgreSQL system administrator. If you don't have a system administrator or if you want to become your own system
administrator follow the instructions below.

Installing a PostgreSQL server
------------------------------

If you don't already have a PostgreSQL server running on your local machine (or accessible over the network) follow
these instructions.

Go to the computer you want to install the server on. Ideally this would be a dedicated machine able to handle a
considerable amount of network traffic. For testing purposes or for small-scale deployment infrastructures a normal
computer should be able to do the job.

Download and install the PostgreSQL installer following the instructions here: https://www.postgresql.org/download/
(Jumbo has been tested on PostgreSQL 10.* for Windowsx86-64)

During the installation process you might get asked to set a password for the database superuser: all PostgreSQL databases have a default superuser called 'postgres', with admin rights. Set a password of your choice (e.g. 'postgres') and remember it. In the rest of the tutorials any reference to the 'PostgreSQL system administrator' just means whoever has access to this 'postgres' account.

Now lets check that everything is working properly:

- you now have a PostgreSQL server running on your local machine
- you now have a (super)user called postgres allowed to access the server

You can now connect to the server by running the following in a terminal:

    .. code-block:: postgresql

        psql -U postgres -h localhost

or more generally:

    .. code-block:: postgresql

        psql -U DATABASE_USERNAME -h DATABASE_HOST

Creating a database on your PostgreSQL server
---------------------------------------------

Once you have made a server you need to create databases, on which to save data. (Server > Databases > Tables)

By default, a PostgreSQL server comes with an empty database already initialized called 'postgres' (very imaginative
with the names ...). Let's ignore it for the moment and create our own database on the server. To do this, run the
following command after having connected to the server with your user account:

    .. code-block:: postgresql

        -- Create the database, let's call it 'jumbo_tutorial'
        CREATE database jumbo_tutorial;

Then list all available databases on the server to check it all worked:

    .. code-block::

        \l

In the future, you can now connect directly to your database running the following in a terminal:

    .. code-block:: postgresql

        psql -U postgres -h localhost -d jumbo_tutorial

or more generally:

    .. code-block:: postgresql

        psql -U DATABASE_USERNAME -h DATABASE_HOST -d DATABASE_NAME


Creating a custom database user
---------------------------------------------

All good up to now, but we have been doing everything using the superuser called 'postgres'. If other people want to
connect to the database to pull/upload data they should obviously not be using the 'postgres' superuser account but have
their own. Let's see how to do that.

Let's say we have a person called lienz who read this tutorial and when asked to contact the PostgreSQL system
administrator came to you - as they should! Here is what to do:

Connect to the server as admin from terminal:

    .. code-block:: postgresql

        psql -U postgres -h DATABASE_HOST

Now create him a user account (e.g. lienz) and assign him a password (e.g. lienz) by running:

    .. code-block:: postgresql

        CREATE ROLE lienz WITH PASSWORD 'lienz' LOGIN;

He can now log in the server but he wouldn't be able to access databases (and tables within databases). So run the
following to set him up:

    .. code-block:: postgresql

        GRANT ALL PRIVILEGES ON DATABASE jumbo_tutorial TO lienz;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lienz;

Here we grant the user all possible kind of privileges because we trust him - but you might want to be more restrictive.

Note
^^^^

It's more than likely that the user is not connecting to the database from the same computer that is running the server
so DATABASE_HOST will not be localhost but the network address of the server. In that case he might still have trouble
connecting to the server: ask him to tell you his ip address (IPv4 and IPv6) and add them to the server's pg_hba.conf
file (on the machine running the server). The file should be in the PostgreSQL installation folder, in the data
subfolder e.g. C:\\PostgreSQL\\10\\data\\. Modify the file as follows:

    .. code-block::

        -- Go to this section of pg_hba.conf and add the relevant lines

        # TYPE DATABASE USER ADDRESS METHOD

        # IPv4 local connections:
        ...
        host   all   all   xxx.xxx.xx.xxx/32   md5
        ...

        # IPv6 local connections:
        ...
        host   all  all   yyyy:yyyy:yyyy::yyyy:yyyy/128   md5
        ...

Again here we are being very loose with permissions - allowing connections from all users using those IP adresses, and
allowing them to connect to all databases. You might want to be more restrictive.

The .env configuration file
---------------------------

Jumbo automatically extracts our database connection settings from a .env file with the following structure:

   .. code-block::

         DATABASE_HOST = <my_database_host_address>
         DATABASE_USERNAME = <my_database_user_name>
         DATABASE_PASSWORD = <my_database_user_password>
         DATABASE_PORT = <my_database_port>
         DATABASE_NAME = <my_database_name>

This allows to deploy jumbo on different devices while maintaining sensitive information local.

By default jumbo looks for this file in the working directory of the script being run. It is therefore good practice to
always include such a file in the root project directory of any jumbo script you create.

As an example, the .env file that the user from the tutorial above should be creating should look like this:

    .. code-block::

        DATABASE_HOST = <server_network_address or localhost>
        DATABASE_USERNAME = lienz
        DATABASE_PASSWORD = lienz
        DATABASE_PORT = 5432 (this is the default PostgreSQL server port)
        DATABASE_NAME = jumbo_tutorial

Minimal Example
---------------------------

You should now have everything configured as it should. Remember to create a .env file in the root directory of your
project and then test your installation running the following minimal script:

   .. code-block:: python

         import jumbo

         # Initialize database connection
         database = jumbo.database.Database()

         # Open a connection pool.
         with database.open() as pool:

            # Get an individual connection from the pool.
            with pool.connect():

               pass

If everything went well you are now all set-up to use the JumboSQL library! Enjoy!