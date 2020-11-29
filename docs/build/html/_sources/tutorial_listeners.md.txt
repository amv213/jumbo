# 📺 Live Database Streaming


In this tutorial you will learn how to use jumbo to setup a client listening to a PostgreSQL database.

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

In jumbo, listeners are clients subscribed to a database notification channel and triggering custom event handlers on receipt of a NOTIFY from the server. This is especially useful if - for example - the PostgreSQL database has been setup to trigger a NOTIFY every time a new entry is added to a given table. In this way the client can keep track of changes to the table without needing to constantly poll the database table for changes.

A minimal jumbo listener can easily be configured as follows:

    .. code-block:: python

        import jumbo

         # Initialize database connection
        database = jumbo.database.Database()

        # Create a connection pool
        with database.open() as pool:

            # Get individual connections from the pool
            with pool.connect(key=1):

                # Create your custom handler: must have a .on_notify(Database) method implemented.
                handler = jumbo.handlers.NotifyHandler()
                # Create listener
                dumbo = jumbo.handlers.Listener(pool, channel='my_notification_channel', handler=handler, key=1)

                dumbo.run()

In the code above we have first defined a handler defining the action to take on receipt of a NOTIFY by the listener. I this minimal example we use jumbo's handlers.NotifyHandler() which does not do anything except from logging out to the user that no actions have been taken. In short, nothing will happen when the listener will receive a NOTIFY. Then we have defined the Listener itself, to which we assign the handler we have defined above. Finally we also need to pass database connection related arguments to the Listener for it to subscribe to the correct notification channel on which the database is streaming NOTIFYs.

Let's now see an example using a more useful handler, shipped with jumbo:

    .. code-block:: python

        import jumbo

         # Initialize database connection
        database = jumbo.database.Database()

        # Create a connection pool
        with database.open() as pool:

            # Get individual connections from the pool
            with pool.connect(key=1):

                # Create your custom handler: must have a .on_notify(Database) method implemented.
                handler = jumbo.handlers.LastEntryFetcher(pool, audit_table='audit_table', key=1)
                # Create listener
                dumbo = jumbo.handlers.Listener(pool, channel='my_notification_channel', handler=handler, key=1)

                dumbo.run()

Here we have used exactly the same code as in the previous example but swapped handler with jumbo's LastEntryFetcher. This is a builtin handler relying on the presence of an audit table setup on the PostgreSQL database. An audit table is a table in the database always tracking the last entry of in the table it is auditing. For more information on how to setup such a database infrastructure see the end of this tutorial. With such an audit table in place, jumbo's LastEntryFetcher will retrieve and log out the (one and only) entry in that table - effectively allowing the Listener to have continuous access to the last entry being added to the database table being audited.

Obviously it is also possible to create custom handlers, in order to perform any action desired on receipt of a NOTIFY from the Listener. It is good practice to do this in jumbo by creating a handler class inheriting from NotifyHandler() and overriding its on_notify() method. LastEntryFetcher is an example of such strategy, so don't hesitate to have a look at the documentation for inspiration.

**Note:** LastEntryFetcher is an extremely handy handler. It is especially useful to perform on-the-fly data analysis on data being streamed to the database. By default, LastEntryFetcher only logs to the user the last entry fetched, but the class exposes a convenient overridable method called process(), to which the last entry fetched is passed. Users can therefore easily implement on-the-fly data analysis by creating a class inheriting from LastEntryFetcher and overriting its 'process' method. Let's see a trivial example:

    .. code-block:: python

        import jumbo
        import loguru

        # A custom LastEntryFetcher
        def CustomLastEntryFetcher(jumbo.handlers.LastEntryFetcher):

            def __init__(self, database, audit_table, constant, key=1):

                # Inherit
                super().__init__(database, audit_table, key)

                # Can add custom attributes
                self.constant = constant

            # Add data analysis step
            def process(self, last_entry):
                """Called on each last-entry fetch.

                Overwriting method of parent class"""

                # very trivial example
                loguru.logger(f"Handler fetched {last_entry} and is also logging out {self.constant}")


                # but could do operations here on last_entry and e.g. write results to another database table...


        if __name__ == "__main__":

         # Initialize database connection
        database = jumbo.database.Database()

            # Create a connection pool
            with database.open() as pool:

                # Get individual connections from the pool
                with pool.connect(key=1):

                    # Create your custom handler: must have a .on_notify(Database) method implemented.
                    handler = CustomLastEntryFetcher(pool, audit_table='audit_table', key=1)
                    # Create listener
                    dumbo = jumbo.handlers.Listener(pool, channel='my_notification_channel', handler=handler, key=1)

                    dumbo.run()

Setting up an audit table
--------------------------

Jumbo Listeners are a very handy tool but the PostgreSQL database should be setup to be streaming NOTIFYs on a notification channel. Moreover, in order to expolit jumbo's LastEntryFetcher, there should be a table on the database being audited, and a NOTIFY being triggered every time new data is inserted into such table. Please find below a SQL template to execute to such a database configuration, but do not hesitate to browse the PostgreSQL documentation to modify it and create your own variants:

    .. code-block:: postgresql

        -- Create audit table, using the table being audited as template
        CREATE TABLE IF NOT EXISTS audit_table AS
            TABLE table LIMIT 1;

        -- Define trigger function
        CREATE OR REPLACE FUNCTION audit_and_notify()
        RETURNS trigger AS $$
        BEGIN

            -- update all rows in the audit table (there is only one) with NEW values. Here NEW is unpacked with special ().* sintax
            UPDATE audit_table
            SET    (table_column1, table_column2, ...) = (SELECT (NEW).*);

            -- send a NOTIFY to clients listening. Jumbo Listeners should then set channel='channel'
            NOTIFY channel;

            RETURN NULL;

        END;
        $$ LANGUAGE plpgsql;

        -- Drop TRIGGER just in case one already exists
        DROP TRIGGER trigger_audit ON table;

        -- Create trigger on table
        CREATE TRIGGER trigger_audit
        AFTER INSERT
        ON table
        FOR EACH ROW
        EXECUTE PROCEDURE audit_and_notify();