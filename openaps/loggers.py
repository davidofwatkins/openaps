import logging
import sys
import os
import openaps

def setup_logging(logger):

  log_git = openaps.get_config_var('logging', 'log_with_git')
  logfile = openaps.get_config_var('logging', 'logfile')

  logger.setLevel(logging.DEBUG)

  # log everything to stdout
  stream_handler = logging.StreamHandler()
  stream_handler.setLevel(logging.DEBUG)
  stream_handler.setFormatter(logging.Formatter())
  logger.addHandler(stream_handler)

  # also log everything to our log file
  if logfile:
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s', '%Y-%m-%d %H:%M:%S'))
    logger.addHandler(file_handler)

  # if enabled, log as git commits as well
  if log_git:
    logger.addHandler(GitHandler())

  # handle any uncaught exceptions so that they're logged
  def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical('Unhandled Exception: %s', exc_value, exc_info=(exc_type, exc_value, exc_traceback))

  sys.excepthook = handle_uncaught_exception

class GitHandler(logging.NullHandler):
  """ A handler to log via Git
  
  Passes logs on to Git for LogRecords with log_git=True.
  To use, logg with extra={ 'log_git': True }). For example:

  logger.debug('This is will be committed to Git!', extra={ 'log_git': True })
  
  Extends:
    logging.NullHandler
  """
  repo = None

  def handle(self, record):
    if not hasattr(record, 'log_git') or not record.log_git: return
    self.app.create_git_commit(record.getMessage())

  def git_repo(self):
    """ Get the current Git Repo and set it to self.repo
  
      Returns:
        Repo instance
    """
    from git import Repo, GitCmdObjectDB, InvalidGitRepositoryError
    try:
      self.repo = getattr(self, 'repo', Repo(os.getcwd(), odbt=GitCmdObjectDB))
    except InvalidGitRepositoryError:
      self.logger.warning('Warning: Git repo does not exist. Please create one or set log_git to false in your OpenAPS config file.') # @todo:david maybe better explanation with proper way to set config?
      return None

    return self.repo

  def create_git_commit(self, log_msg=''):
    if not self.git_repo(): return

    if self.repo.is_dirty() or self.repo.index.diff(None):
      # replicate commit -a, automatically add any changed paths
      # should help
      # https://github.com/openaps/openaps/issues/87
      diffs = self.repo.index.diff(None)
      for diff in diffs:
        self.repo.git.add([diff.b_path], write_extension_data=False)
        # XXX: https://github.com/gitpython-developers/GitPython/issues/265
        # GitPython <  0.3.7, this can corrupt the index
        # repo.index.add([report.name])
      msg = """{0:s} {1:s}

      TODO: better change descriptions
      {2:s}

      {3:s}
      """.format(self.parser.prog, ' '.join(sys.argv[1:]), log_msg, ' '.join(sys.argv))
      # https://github.com/gitpython-developers/GitPython/issues/265
      # git.commit('-avm', msg)
      self.repo.index.commit(msg)

    self.repo.git.gc(auto=True)
