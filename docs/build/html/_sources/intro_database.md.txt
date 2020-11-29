# 💾 Database Setup


To start using jumbo you need to have a PostgreSQL database to connect to. This can be running on your local machine or
anywhere on your network. You also need to have setup a PostgreSQL user account with appropriate privileges to access
that database. If you are unsure about what any of the previous sentence actually means get in touch with your
PostgreSQL system administrator. If you don't have a system administrator or if you want to become your own system
administrator follow the instructions below.

## 🐘 Installing a PostgreSQL server


If you don't already have a PostgreSQL server running on your local machine (or accessible over the network) follow
these instructions.

Go to the computer you want to install the server on. Ideally this would be a dedicated machine able to handle a
considerable amount of network traffic. For testing purposes or for small-scale deployment infrastructures a normal
computer should be able to do the job.

Download and install the PostgreSQL installer following the instructions
 [here](https://www.postgresql.org/download/)

During the installation process you might get asked to set a password for the database superuser: all PostgreSQL
databases have a default superuser called `postgres`, with admin rights. Set
 a password of your choice (e.g. *postgres*) and remember it. In the rest of
  the tutorials any reference to the *PostgreSQL system administrator* just
   means whoever has access to this `postgres` account.

Now lets check that everything is working properly:

- you should now have a PostgreSQL server running on your local machine
- you should now have a (super)user called postgres allowed to access the
 server

You can now connect to the server by running the following in a terminal:

```bash
psql -U postgres -h localhost
```

or more generally:

```bash
psql -U DATABASE_USERNAME -h DATABASE_HOST
```

## 📮 Creating a database


Once you have made a server you need to create databases, on which to save 
data.

By default, a PostgreSQL server comes with an empty database already 
initialized, and called `postgres`. Let's ignore it for the moment and
let's create our own database on the server. To do this, run the
following command after having connected to the server with your user account:

```postgresql
-- Create the database, let's call it 'jumbo_tutorial'
CREATE database jumbo_tutorial;
```

Then list all available databases on the server to check it all worked:

```bash
\l
```

In the future, you can now connect directly to your database running the 
following in a terminal:

```bash
psql -U postgres -h localhost -d jumbo_tutorial
```

or more generally:

```bash
psql -U DATABASE_USERNAME -h DATABASE_HOST -d DATABASE_NAME
```

## 👷 Adding a user


All good up to now, but we have been doing everything using the superuser 
called `postgres`. If other people want to connect to the database to pull
/upload data they should obviously not be using the `postgres` superuser 
account but have their own. Let's see how to do that.

Let's say we have a user called `wilma` who read this tutorial and when
 asked to contact the PostgreSQL system administrator came to you - as they
  should! Here is what to do:

Connect to the server as admin from terminal:

```bash
psql -U postgres -h DATABASE_HOST
```

Now create the user an account (e.g. `wilma`) and assign them a password (e
.g. `wilma_superstar`) by running:

```postgresql
CREATE ROLE wilma WITH PASSWORD 'wilma_superstar' LOGIN;
```

### 🔓 Granting permissions

The user account we have just created can log in the server, but wouldn't be
able to access our database (and tables within the database). Run
the following to set them up:

```postgresql
GRANT ALL PRIVILEGES ON DATABASE jumbo_tutorial TO wilma;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wilma;
```

```{note}
Here we grant the user all possible kind of privileges because we trust him - 
but you might want to be more restrictive.
```

It's more than likely that the user is not going to connect to the database
from the same computer that is running the server. In that case they might
still have trouble connecting to the server: ask them to tell you their ip
 address (IPv4 and IPv6) and add them to the server's `pg_hba.conf`
file (on the machine running the server). The file should be in the 
PostgreSQL installation folder, in the data subfolder e.g. `C:\\PostgreSQL
\\10\\data\\`. Modify the file as follows:

```text
...

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
```

```{note}
Again here we are being very loose with permissions - allowing connections 
from all users using those IP adresses, and allowing them to connect to all
databases. You might want to be more restrictive.
```

Your user should now be able to use the jumbo library storing on their
 computer the following `jumbo.env` configuration file:

```
DATABASE_HOST = <server_network_address or localhost>
DATABASE_USERNAME = wilma
DATABASE_PASSWORD = wilma_superstar
DATABASE_PORT = 5432 (this is the default PostgreSQL server port)
DATABASE_NAME = jumbo_tutorial
```