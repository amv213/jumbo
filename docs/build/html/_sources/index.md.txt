# 📑 Welcome to Jumbo!

Jumbo is a wrapper of the amazing [`psycopg2`](https://www.psycopg.org/) - 
the most popular [PostgreSQL](https://www.postgresql.org/) database adapter 
for the Python programming language.

Jumbo has been designed specifically for adoption in environments where
thorough widespread knowledge of SQL protocols might be lacking and a
streamlined approach to database interactions might be needed. Jumbo offers an
intuitive and quickly deployable interface to successfully implement a
database-centred data analysis pipeline at all levels of your team or
organisation.

Jumbo is intuitive yet customisable - first-time users can easily interact
with the database without worrying about handling transactions under the hood.
At the same time, experienced PostgreSQL architects can still unleash the full
power of `psycopg2` and exploit its more advanced functionalities.

If it's your first time using jumbo head over to [First Steps](intro_package.md) 
to setup your installation environment. If you are already familiar with
 jumbo simply follow the {ref}`Quick Start <index/quick-start>` guide below.

---

(index/quick-start)=
## 🚀 Quick Start

1. 📚 Install jumbo like any other Python package, using pip to download it
 from PyPI:

    >```bash
    >pip install jumbo
    >```

2. 🐘 Make sure you have created a `jumbo.env` file in the root directory of
 your project with the following structure:

    >```
    >DATABASE_HOST = <my_database_host_address>
    >DATABASE_USERNAME = <my_database_user_name>
    >DATABASE_PASSWORD = <my_database_user_password>
    >DATABASE_PORT = <my_database_port>
    >DATABASE_NAME = <my_database_name>
    >```

3. 🐍 Now test your installation running the following minimal script:

    >```python
    >import jumbo
    >
    ># Initialize database connection
    >database = jumbo.database.Database()
    >
    ># Open a connection pool.
    >with database.open() as pool:
    >
    >    # Get an individual connection from the pool.
    >    with pool.connect():
    >
    >        pass
    >``` 

4. 🎉 If everything went well you are now all set-up to use the Jumbo SQL
 library! Enjoy!

---

## 📚 Table of Contents


```{toctree}
:caption: MAIN DOCS
:maxdepth: 2

First Steps <intro_package.md>
Database Setup <intro_database.md>
Documentation <documentation.md>
```

```{toctree}
:caption: TUTORIALS
:maxdepth: 2

Basic Usage <tutorial_basic.md>
Watchdogs <tutorial_watchdogs.md>
Listeners <tutorial_listeners.md>
```