import logging
import jumbo.config
import jumbo.database
import jumbo.handlers
import jumbo.utils

logger = logging.getLogger(__name__)
logger.setLevel("WARNING")  # best practice

# Uncomment if want to prevent the library’s logged events being output to
# sys.stderr in the absence of user-side logging configuration
# logger.addHandler(logging.NullHandler())
