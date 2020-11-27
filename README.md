![jumbo logo](./docs/imgs/logo.png)

# 📑 Welcome to Jumbo!

Jumbo is a wrapper of the amazing [`psycopg2`](https://www.psycopg.org/) - the
 most
 popular [PostgreSQL](https://www.postgresql.org/) database adapter for the
  Python programming language. 
 
 Jumbo has been designed specifically for adoption in
  environments where thorough widespread knowledge of SQL protocols might
   be lacking and a streamlined approach to database interactions might be
    needed. 
Jumbo offers an intuitive and quickly deployable interface to successfully
 implement a database-centred data analysis pipeline at all levels of your
  team or organisation. 
  
  Jumbo is intuitive yet customisable - first-time users can 
  easily interact with the database without worrying about handling
   transactions under the hood. At the same time, experienced PostgreSQL
    architects can
    still
    unleash the full power of `psycopg2` and exploit its more advanced
     functionalities.

## 🚀 Quick Start

1. 📚 Install jumbo like any other python package, using pip to download it
 from PyPI:

    ```cmd
        $ pip install jumbo
    ```

2. 🐘 Create a `jumbo.env` file in the root directory of your project with
 the
 following structure:
    
    ```.env
        DATABASE_HOST = <my_database_host_address>
        DATABASE_USERNAME = <my_database_user_name>
        DATABASE_PASSWORD = <my_database_user_password>
        DATABASE_PORT = <my_database_port>
        DATABASE_NAME = <my_database_name>
    ```

3. 🐍 Test your installation running the following minimal script:
    
    ```python
         import jumbo
    
         # Initialize database connection
         database = jumbo.database.Database()
    
         # Open a connection pool.
         with database.open() as pool:
    
            # Get an individual connection from the pool.
            with pool.connect():
    
               pass
    ```
   
## 📚 Documentation

To learn more about the package head over to the [official documentation](https://amv213.gitlab.io/jumbo/)!