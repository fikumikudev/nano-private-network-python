import logging

from rich.logging import RichHandler

logging.basicConfig(format="%(message)s", level=logging.DEBUG, handlers=[RichHandler()])
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
