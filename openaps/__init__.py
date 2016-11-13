"""
Release notes:

* 0.1.0 - transition to Exported interfaces, utilize pkg_resources
          more for advertisements of openaps capabilities across the
          python environment.  Also, rely more on json import/export
          of configuration.  Also, variety of git tweaks.
"""
__version__ = '0.2.0-dev'

import sys
import logging
import os
from loggers import setup_logging
from json import loads
from ConfigParser import NoOptionError, NoSectionError
import config

_active_config = None


def get_config_path():
  """ Get the path to our config file, if available. """

  cfg_file = os.environ.get('OPENAPS_CONFIG', 'openaps.ini')
  if not os.path.exists(cfg_file):
    return None

  return cfg_file

def read_config():
  """ Global method that allows any OpenAPS code to retrieve the user's config.
  Requires the OPENAPS_CONFIG environment variable to be set or an openaps.ini file in the
  current working directory. """

  global _active_config
  if _active_config: return _active_config

  cfg_file = get_config_path()
  if not cfg_file:
    # We should always have a cfg_file at this point because we only let very limited commands
    # through openaps.run() without a set config file. But just in case:
    raise Exception("Unable to find openaps config: %s" % cfg_file)

  pwd = os.getcwd( )
  cfg_dir = os.path.dirname(cfg_file)
  if cfg_dir and os.getcwd( ) != cfg_dir:
    os.chdir(os.path.dirname(cfg_file))
    
  _active_config = config.Config.Read(cfg_file)
  return _active_config

def get_config_var(section, option, default=None, type=None):
  """ Convenience method for quickly retrieving a config variable from our active config.
  
  Arguments:
    section {string} -- The section to look in from the config file
    option {string} -- The name of the option to retrieve
  
  Keyword Arguments:
    default {*} -- The value to return if the option cannot be found (default: {None})
    type {string} --  What type of value to retrieve. If not set, this will attempt to
                      return a number, boolean, or string automatically (default: {None})
  
  Returns:
    A string, boolean, or number, retrieved from the openaps config.
  """

  config = read_config()
  if not config: return None

  # Try to get the config if section exists
  try:
    if type == 'boolean': return config.getboolean(section, option)
    if type == 'int': return config.getint(section, option)
    if type == 'float': return config.getfloat(section, option)

    value = config.get(section, option)
  except (ValueError, NoSectionError, NoOptionError):
    return default
  
  # If no type set, try to parse it as JSON:
  try: value = loads(value)
  except ValueError: pass
  return value

# Initialize logging, if there is a config file
if get_config_path():
  # pass our logger to setup_logging() so it uses the global openaps logger, not openaps.loggers
  setup_logging(logging.getLogger(__name__))