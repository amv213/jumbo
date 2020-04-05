from os import environ, path, getcwd
from dotenv import load_dotenv


class Config:
    """Configuration class setting global environment variables to connect to a PostgreSQL database via Jumbo.

    Variables are extracted from an existing .env file defining the following variables::
    
        DATABASE_HOST = the PostgreSQL server host address
        DATABASE_USERNAME = the PostgreSQL username of the user connecting to the database
        DATABASE_PASSWORD = the PostgreSQL password of the user connecting to the database
        DATABASE_PORT = the port on which the PostgreSQL server is running (usually 5432)
        DATABASE_NAME = the name of the database to which to connect

    By default, the .env file should be located in the root working directory of the script invoking the constructor.
    """

    def __init__(self, env_path=None):
        """Initializes configuration settings in order to connect to a PostgreSQL database with jumbo.

        Args:
            env_path (string, optional):    path where to look for the configuration file (.env). Defaults to current
                                            working directory of script invoking this constructor.
        """
        # Look for .env in provided path. Else in working directory of script invoking constructor
        env_path = env_path if env_path is not None else getcwd()
        dotenv_path = path.join(env_path, 'jumbo.env')

        load_dotenv(dotenv_path)

        # Set instance attributes
        self.ENV_PATH = dotenv_path
        self.DATABASE_HOST = environ.get('DATABASE_HOST')
        self.DATABASE_USERNAME = environ.get('DATABASE_USERNAME')
        self.DATABASE_PASSWORD = environ.get('DATABASE_PASSWORD')
        self.DATABASE_PORT = environ.get('DATABASE_PORT')
        self.DATABASE_NAME = environ.get('DATABASE_NAME')

    def __repr__(self):
        """A debugging-friendly representation of the object.

        Returns:
            (string): representation of the Config object.
        """

        return f"{self.__class__} ({self.__dict__})"

    def __str__(self):
        """A human-friendly pretty-print representation of the object.

        Returns:
            (string): annotated representation of the Config object.
        """

        return ("\nDATABASE CONFIGURATION SETTINGS:\n"
                "ENV_PATH:\t{ENV_PATH}\n"
                "DATABASE_HOST:\t{DATABASE_HOST}\n"
                "DATABASE_PORT:\t{DATABASE_PORT}\n"
                "DATABASE_NAME:\t{DATABASE_NAME}\n"
                "DATABASE_PASSWORD:\txxx\n"
                "DATABASE_USERNAME:\t{DATABASE_USERNAME}\n"
                ).format(**self.__dict__)
