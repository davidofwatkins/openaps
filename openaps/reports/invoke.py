
"""
invoke   - generate a report
"""
from __future__ import print_function
import reporters
import sys

def configure_app (app, parser):
  """
  """
  parser._actions[-1].nargs = '+'

def main (args, app):
  # print args.report
  # print app.parser.parse_known_args( )
  requested = args.report[:]
  for spec in requested:
    report =  app.actions.selected(args).reports[spec]
    device = app.devices[report.fields['device']]
    task = app.actions.commands['add'].usages.commands[device.name].method.commands[report.fields['use']]
    # print(task.name, task.usage, task.method, report.fields, app.inputs)
    # print device.name, device
    # print report.name, report.fields
    # XXX.bewest: very crude, need to prime the Use's args from the config
    app.parser.set_defaults(**task.method.from_ini(report.fields))
    args, extra = app.parser.parse_known_args(app.inputs)
    """
    for k, v in report.fields.items( ):
      setattr(args, k, v)
    """

    try:
        output = task.method(args, app)
    except Exception as e:
        # log and save prior progress in git
        app.logger.exception('%s raised %s' % (report.name, e), extra={ 'log_git': True })
        sys.exit(1) # ensure we still blow up with non-zero exit
    else:
        reporters.Reporter(report, device, task)(output)
        app.logger.info('invoked report %s (%s)' % (report.name, report.format_url()), extra={ 'log_git': True })
