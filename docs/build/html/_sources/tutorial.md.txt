# 📋 First Steps

## 🐍 Installing jumbo

You can install jumbo like any other Python package, using `pip` to download it 
from PyPI:

```bash
pip install jumbo
```

or by downloading the source package locally and building the `setup.py` file:

```bash
python setup.py build
sudo python setup.py install
```


## 🐘 The `jumbo.env` configuration file

Jumbo automatically extracts our database connection settings from a 
`jumbo.env` file with the following structure:

```
DATABASE_HOST = <my_database_host_address>
DATABASE_USERNAME = <my_database_user_name>
DATABASE_PASSWORD = <my_database_user_password>
DATABASE_PORT = <my_database_port>
DATABASE_NAME = <my_database_name>
```

This allows to deploy jumbo on different devices while maintaining sensitive 
information local. By default jumbo looks for this file in the working
 directory of the script being run. 
 
 ```{tip}
 If you are sharing code with others, make sure to add the `jumbo.env
` file to your `.gitignore`. Alternatively, you can also hide your
 configuration file in a private folder and point jumbo to it later on.
```


## 🔮 Testing your environment

If you already have a PostgreSQL database [up and running](database.md), you
 are good to go! For now put your `jumbo.env` file in the root directory of
  your project and then test your installation running the following minimal
   script:

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

If everything went well you are now all set-up to use the Jumbo SQL library
! Enjoy!