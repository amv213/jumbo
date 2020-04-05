
.. jumbo documentation master file, created by
   sphinx-quickstart on Sun Mar 29 13:19:49 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. figure:: ../imgs/logo.png
   :scale: 20 %
   :align: center
   :alt: Jumbo SQL Banner

.. _index:

Welcome to jumbo's documentation!
=================================

Welcome to jumbo! The PostgreSQL library for scientist.

Jumbo is a wrapper of psycopg2 - the most popular PostgreSQL database adapter for the Python programming language. Jumbo
has been designed specifically for adoption in scientific research environments, where thorough widespread knowledge of
SQL protocols might be lacking and a streamlined approach to database interactions might be needed. Jumbo offers an
intuitive and quickly deployable interface to successfully implement a database-centred data analysis pipeline at all
levels of the organisation. Jumbo is intuitive yet customizable - first-time users can easily interact with the database
without worrying about handling transactions under the hood, while experienced PostgreSQL architects can unleash the
full power of jumbo to exploit advanced PostgreSQL functionalities.

If it's your first time using jumbo head over to *First Steps* to setup your installation environment. If you are
already familiar with jumbo simply follow the *Quick Start* guide below.

Quick Start
=================================

Install jumbo like any other Python package, using pip to download it from PyPI:

    .. code-block:: python

        pip install jumbo==0.0.2b

Make sure you have created a jumbo.env file in the root directory of your project with the following structure:

   .. code-block::

         DATABASE_HOST = <my_database_host_address>
         DATABASE_USERNAME = <my_database_user_name>
         DATABASE_PASSWORD = <my_database_user_password>
         DATABASE_PORT = <my_database_port>
         DATABASE_NAME = <my_database_name>

Now test your installation running the following minimal script:

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

Table of Contents
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   First Steps <tutorial>
   Demos <demos>
   Documentation <modules>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
