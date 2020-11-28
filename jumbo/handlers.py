import time
import logging
import eventlet
from abc import ABC
from psycopg2 import sql
from pygtail import Pygtail
from .database import Database
from psycopg2.extras import DictRow
from eventlet.hubs import trampoline
from typing import Union, List, Optional, NoReturn
from watchdog.observers.polling import PollingObserver, PollingEmitter
from watchdog.events import PatternMatchingEventHandler, FileSystemEvent

# Spawn module-level logger
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# WATCHDOGS
# -----------------------------------------------------------------------------


# TODO: Overwrite PollingEmitter(BaseEmitter(BaseThread(thread.Thread))) to
#  behave appropriately when thread stopped
def mod_on_thread_start(self: PollingEmitter) -> None:
    """Override this method instead of :meth:`start()`.
    :meth:`start()` actually calls this method.

    This method is called right before this thread is started and this
    object’s run() method is invoked.

    Args:
        self: PollingEmitter object
    """

    # PollingEmitter's on_thread_start
    self._snapshot = self._take_snapshot()


def mod_on_thread_stop(self: PollingEmitter) -> None:
    """Override this method instead of :meth:`stop()`.
    :meth:`stop()` actually calls this method.

    This method is called immediately after the thread is signaled to stop.

    Args:
        self: PollingEmitter object
    """

    pass

# Mod behaviour with changes above
PollingEmitter.on_thread_start = mod_on_thread_start
PollingEmitter.on_thread_stop = mod_on_thread_stop


class FileWatcher:
    """Watchdog periodically polling a directory for file changes and
    streaming updates to PostgreSQL database.

    Example:

        .. code-block:: python

            # Template SQL command to execute on trigger
            query = 'INSERT INTO table_name ' \
                    '(column_name, another_column_name) VALUES (%s, %s)'

            # Create watchdog
            fido = FileWatcher(jumbo.database.Database(),
                               SQL_INSERT_IN_TABLE, 'data/',
                               patterns = ["*.txt"], timeout=0.5)

            # Deploy watchdog
            fido.bark()
    """

    def __init__(self, database: Database, query: Union[str, sql.Composed],
                 src_path: str, recursive: bool = True, timeout: float = 1.0,
                 patterns: Optional[List[str]] = None,
                 ignore_directories: bool = False, key: int = 1) -> None:
        """Initializes polling watchdog with event handler streaming
        filesystem changes to PostgreSQL database.

        Args:
            database:                       jumbo's PostgreSQL database
                                            connection manager. Needs an
                                            open connection pool with at
                                            least an active connection.
            query:                          SQL query to execute on watchdog
                                            trigger when passed new file
                                            contents.
            src_path:                       directory to poll and monitor for
                                            changes
            recursive (optional):           True if watchdog should poll
                                            recursively into src_path.
            timeout (optional):             interval in seconds between
                                            polling the file system
            patterns (optional):            list of file-name patterns to
                                            monitor for changes in the
                                            directory
            ignore_directories (optional):  True if directory names matching
                                            *patterns* should be ignored.
                                            False otherwise.
            key (optional):                 key of the pool connection being
                                            used in the transaction. Defaults
                                            to [1].
        """

        # TODO: check src_path exists
        self.src_path = src_path
        self.recursive = recursive
        self.event_observer = PollingObserver(timeout=timeout)
        self.event_handler = InsertToSQL(database, query, patterns=patterns,
                                         ignore_directories=ignore_directories,
                                         key=key)

    def bark(self) -> NoReturn:
        """Schedules and starts the watchdog.

        The script's main thread is kept alive in an infinite while loop,
        while the watchdog starts periodically polling the filesystem for
        changes on a separate thread. A third concurrent thread is released
        from lock and executes every time a change has been detected.
        """

        # spawns two new threads, one for the observer polling and one for
        # the event_handler acting (the handler is locked until triggered.
        # It executes and then relocks.)
        self.start()

        try:
            
            # Keep alive main thread  with while loop
            while True:

                # Main Loop.
                # Watchdog is polling every TIMEOUT seconds on another thread
                time.sleep(1)

        # TODO: this seems to never get raised/caught. Implement advanced
        #  SIGINT concurrent threads handling
        except (Exception, KeyboardInterrupt) as e:
            logger.warning(f"Error raised while running watchdog: {e}")

        finally:
            self.stop()

    def start(self) -> None:
        """Schedule and starts concurrent watchdog observer threads."""

        # Schedule observer
        self.event_observer.schedule(self.event_handler, self.src_path,
                                     recursive=self.recursive)
        # Start watchdog thread; can give it name with observer.set_name()
        self.event_observer.start()

    def stop(self) -> None:
        """Stops watchdog threads."""

        self.event_observer.stop()
        self.event_observer.join()


class InsertToSQL(PatternMatchingEventHandler):
    """Event handler firing whenever a filesystem modification is detected.
     Executes arbitrary SQL query on trigger."""

    def __init__(self, database: Database, query: Union[str, sql.Composed],
                 patterns: Optional[List[str]] = None,
                 ignore_patterns: Optional[List[str]] = None,
                 ignore_directories: bool = True,
                 case_sensitive: bool = True, key: int = 1) -> None:
        """Initialize event handler.

        Args:
            database:                       jumbo's PostgreSQL database
                                            connection manager. Needs an open
                                            connection pool with at least an
                                            active connection.
            query:                          SQL query to execute on watchdog
                                            trigger when passed new file
                                            contents.
            patterns (optional):            list of file-name patterns to
                                            monitor for changes in the
                                            directory
            ignore_patterns (optional):     patterns to ignore matching event
                                            paths
            ignore_directories (optional):  ``True`` if directory names
                                            matching *patterns* should be
                                            ignored. ``False`` otherwise.
            case_sensitive (optional):      ``True`` if path names should be
                                            matched sensitive to case;
                                            ``False`` otherwise.
            key (optional):                 key of the pool connection being
                                            used in the transaction. Defaults
                                            to [1].
        """
        # Look for changes in txt files by default
        patterns = ["*.txt"] if patterns is None else patterns

        # Call PatternMatchingEventHandler constructor
        super().__init__(patterns, ignore_patterns, ignore_directories,
                         case_sensitive)

        # Add custom methods related to jumbo's Database
        self.pool = database
        self.key = key
        self.query = query

    # The following filesystem event_type exist:
    # 'moved', 'deleted', 'created', 'modified'
    # Here we handle only the default callback for 'modified' event
    # which will be triggered under the hood only for files matching pattern
    def on_modified(self, event: FileSystemEvent) -> None:
        """Overwrites default on_modified event trigger fired when filesystem
        modification detected.

        Here we want to ignore taking action if a filesystem directory has
        been modified (only want to act on files).

        Args:
            event:    watchdog event
        """

        # And decide to only watch for file changes
        if not event.is_directory:

            # Process event (i.e send SQL)
            self.process_event(event)

    def process_event(self, event: FileSystemEvent) -> None:
        """Function handling what happens to an event raised by the watchdog:
        here we write any file changes as new entries in a database table.

        Args:
            event:    watchdog event
        """

        logger.debug(f"Event detected: {event.event_type} {event.src_path}")

        # Use Pygtail to return unread (i.e.) new lines in modified file
        for line in Pygtail(event.src_path):
            # remember tuple formatting   v   (see psycopg2 docs)
            self.pool.send(self.query, (line, ), key=self.key)

# -----------------------------------------------------------------------------
# LISTENERS
# -----------------------------------------------------------------------------


class Listener:
    """A concurrent thread manager listening for PostgreSQL database NOTIFYs
    on a given channel. On receipt of a notify a custom event handler takes
    action.

    Example:

        .. code-block:: python

            # Choose handler: must have a .on_notify(self) method implemented.
            handler = jumbo.handlers.LastEntryFetcher(jumbo_Database,
                                                      audit_table)
            # Create listener triggering handler's .on_notify(self) on NOTIFY
            dumbo = jumbo.handlers.Listener(jumbo_Database,
                                            channel='table_changed',
                                            handler=handler)
            # Run threads
            dumbo.run()
    """
    
    def __init__(self, database: Database, channel: str,
                 handler: 'NotifyHandler', key: int = 1) -> None:
        """Initialises listener for PostgreSQL database NOTIFYs on given
        channel. The given event handler takes action on receipt of
        notification.

        Args:
            database:       jumbo's PostgreSQL database connection manager.
                            Needs an open connection pool with at least an
                            active connection.
            channel:        name of the channel on which PostgreSQL is sending
                            NOTIFYs
            handler :       handler fired on receipt of ech notify. Should
                            have a .on_notify(self) method defined.
            key (optional): key of the pool connection being used in the
                            subscription transaction. Defaults to [1].
        """

        self.database = database
        self.channel = channel
        self.handler = handler
        self.key = key

    def run(self) -> NoReturn:
        """Spawns a greenthread subscribing to PostgreSQL database
        notification channel and waits for NOTIFYs. On receipt the thread is
        blocked and the Listener.handler() is fired. Once the handler has
        finished processing the thread is finally unblocked and waits for
        the next NOTIFY.
        """

        # multi-producer, multi-consumer queue that works across greenlets
        # size 1 (i.e. not infinite) so that it blocks until entry processed
        queue = eventlet.Queue(0)
        # spawn async greenthread in parallel
        g = eventlet.spawn(self.subscribe, queue)

        while True:

            try:

                logger.debug(f"Waiting for a notification...")
                notify = queue.get()
                # ^ blocks until item available in queue. i.e. waiting for
                # spawned function to yield
                # ----------------%--------------------%----------------------#

                logger.info(f"Got NOTIFY: "
                            f"{notify.pid} {notify.channel} {notify.payload}")

                # do something with the database once received the NOTIFY (n)
                self.handler.on_notify()

                # tell queue that this consumer has finished the task for
                # which it asked q.get()
                queue.task_done()
                # block until all items in the queue have been gotten and
                # processed:
                queue.join()

            except KeyboardInterrupt:
                eventlet.kill(g)
                logger.error("Listener has been killed via Keyboard "
                             "Interrupt. Greenthread garbage collected.")
                break

    def subscribe(self, q: eventlet.Queue) -> NoReturn:
        """Green thread process waiting for NOTIFYs on the channel and feeding
        them to the queue.

        Args:
            q:  event queue through which to pipe NOTIFY events to the main
                thread.
        """

        # Subscribe to notification channel
        self.database.listen_on_channel(self.channel, self.key)

        # Infinite listening loop
        while True:

            # self.database.pool._used[self.key] is the connection object
            # corresponding to [key] in the conneciton pool

            # spawns a green thread and return control once there is a
            # notification to read
            trampoline(self.database.pool._used[self.key], read=True)

            # once there is a notification --> poll
            self.database.pool._used[self.key].poll()

            while self.database.pool._used[self.key].notifies:
                # extract notify:
                notify = self.database.pool._used[self.key].notifies.pop()
                # block until slot available in queue to insert Notify:
                q.put(notify)
                # ----------------%--------------------%----------------------#


class NotifyHandler(ABC):
    """Abstract Handler managing actions performed on reception of a NOTIFY
    from the database. Inherit from it to define your own custom handlers."""

    def __init__(self) -> None:

        pass

    def on_notify(self) -> None:
        """Procedure to execute once a NOTIFY is received.

        Overwrite as needed"""

        logger.debug(f"No actions taken on reception of NOTIFY.")


class LastEntryFetcher(NotifyHandler):
    """Custom handler which fetches las entry in a PostgreSQL audit table on
    trigger.
    """

    def __init__(self, database: Database, audit_table: str, key: int = 1):
        """Initialises custom handler.

        Args:
            database:       jumbo's PostgreSQL database connection manager.
                            Needs an open connection pool with at least an
                            active connection.
            audit_table:    name of PostgreSQL database 'audit' table. Should
                            have been configured to always contain a single
                            row corresponding to the latest row added to the
                            table it is auditing (e.g. configuring a TRIGGER
                            on that table).
            key (optional): key of the pool connection being used to fetch last
                            database entry. Defaults to [1].
        """

        super().__init__()

        self.database = database
        self.audit_table = audit_table
        self.key = key

        # SQL query to fetch last (and only) entry in audit table
        self.SQL = sql.SQL('SELECT * FROM {};').format(
            sql.Identifier(self.audit_table))

    def on_notify(self) -> None:
        """Fetch entry that triggered the notify"""

        # send SQL string to PostgreSQL database (fetch method = fetchone())
        iter_results = self.database.send(
            self.SQL, fetch_method=0, key=self.key)

        # Do additional data processing on the fetched results
        self.process(iter_results)

    # Don't make it static, so to be easily overwritable to perform more
    # complex data analysis dependent on self attributes
    def process(self, iter_results: DictRow) -> None:
        """Logs results to console.

        Overwrite if need more complex data analysis on last entry in audit
        table.

        Args:
            iter_results: last entry in table. Can be accessed as dictionary.
        """

        logger.debug(f"These are the last results in the audit "
                     f"table:{iter_results}")
