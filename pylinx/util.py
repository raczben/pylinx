import os
import logging
import pkg_resources


# The version is handled by the package: pbr, which derives the version from the git tags.
try:
    __version__ = pkg_resources.require("wexpect")[0].version
except: # pragma: no cover
    __version__ = '0.0.1.unkowndev0'


def setup_logger():
    """Setup the logger

    The logger reads the `PYSCT_LOGGER_LEVEL` environment variable and set its the verbosity level
    based on that variable. The default is the WARNING level."""

    try:
        logger_level = os.environ['PYLINX_LOGGER_LEVEL']
        print(logger_level)
    except KeyError as _:
        logger_level = logging.INFO

    logger = logging.getLogger('pylinx')
    logger.setLevel(logger_level)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    format = '%(message)s'
    formatter = logging.Formatter(format)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    fh = logging.FileHandler('pylinx.log', 'w', 'utf-8')
    format = '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


class PylinxException(Exception):
    """The exception for this project.
    """
    pass
