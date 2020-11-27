import logging
import jumbo.config
import jumbo.database
import jumbo.handlers
import jumbo.utils

# Setup a basic logger configuration
logging.basicConfig(
    format='[%(asctime)s] (%(name)s) %(levelname)s | %(message)s',
    datefmt='%D %H:%M:%S'
)

# Uncomment if want to prevent the library’s logged events being output to
# sys.stderr in the absence of user-side logging configuration
# logging.getLogger(__name__).addHandler(logging.NullHandler())
