
from ConfigParser import SafeConfigParser
import re
import os
from copy import copy

class Config (SafeConfigParser):
  OPTCRE = re.compile(
          r'\s?(?P<option>[^:=\s][^:=]*)'       # very permissive!
          r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
                                                # followed by separator
                                                # (either : or =), followed
                                                # by any # space/tab
          r'(?P<value>.*)$'                     # everything up to eol
          )
  ini_name = 'openaps.ini'
  
  def __init__(self, *args, **kwargs):
    """ If not otherwise set, allow environment variables to be set in our config.
    useful for storing sensitive info outside of main config """
    if 'defaults' not in kwargs:
      kwargs['defaults'] = os.environ
    SafeConfigParser.__init__(self, *args, **kwargs)
  def set_ini_path (self, ini_path='openaps.ini'):
    self.ini_name = ini_path
  def save (self):
    with open(self.ini_name, 'wb') as configfile:
      self.write(configfile)
  def fmt(self):
      """Write an .ini-format representation of the configuration state."""
      lines = [ ]
      def write (line):
        lines.append(line)
      if self._defaults:
          write("[%s]\n" % DEFAULTSECT)
          for (key, value) in self._defaults.items():
              write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
          write("\n")
      for section in self._sections:
          write("[%s]\n" % section)
          for (key, value) in self._sections[section].items():
              if key == "__name__":
                  continue
              if (value is not None) or (self._optcre == self.OPTCRE):
                  key = " = ".join((key, str(value).replace('\n', '\n\t')))
              write("%s\n" % (key))
          write("\n")
      return "".join(lines)
  def add_device (self, device):
    section = device.section_name( )
    self.add_section(section)
    for k, v in device.items( ):
      self.set(section, k, v)
    if 'extra' in device.fields and getattr(device, 'extra', None):
      extra = Config( )
      extra.set_ini_path(device.fields['extra'])
      extra.add_section(section)
      for k, v in device.extra.items( ):
        extra.set(section, k, v)
      extra.save( )

  def remove_device (self, device):
    section = device.section_name( )
    self.remove_section(section)
  @classmethod
  def Read (klass, name=None, defaults=["/etc/openaps/openaps.ini", os.path.expanduser("~/.openaps.ini"), 'openaps.ini']):
    config = Config( )
    if name:
      config.set_ini_path(name)
      config.read(name)
    else:
      config.set_ini_path('openaps.ini')
      config.read(defaults)
    return config

  def write(self, file):
    """ A hack to not persist our defaults (which we fill with environment vars above)
    to the config file. The defaults aren't otherwise used, so it should be safe to
    wipe them out. """

    tmp_defaults = copy(self._defaults)
    self._defaults = None
    SafeConfigParser.write(self, file)
    self._defaults = tmp_defaults



