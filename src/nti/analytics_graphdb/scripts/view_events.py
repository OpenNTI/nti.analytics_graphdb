#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import sys
import argparse

from nti.analytics.database.resources import get_analytics_db

from nti.analytics_graphdb.utils.view_events import populate_graph_db

from nti.dataserver.utils import run_with_dataserver

from nti.dataserver.utils.base_script import set_site
from nti.dataserver.utils.base_script import create_context

from nti.graphdb import get_graph_db


def _process_args(args):
    set_site(args.site)
    graph = get_graph_db()
    analytics = get_analytics_db()
    count = populate_graph_db(graph, analytics, args.start, args.end)
    logger.info('%s count graph job(s) created', count)


def main():
    arg_parser = argparse.ArgumentParser(description="Upload view events to a graph db.")
    arg_parser.add_argument('-v', '--verbose', help="Be Verbose",
                            action='store_true', dest='verbose')

    arg_parser.add_argument('-s', '--site',
                            dest='site',
                            help="Application SITE.")

    arg_parser.add_argument('-t', '--start',
                            dest='start',
                            help="Starte date.")

    arg_parser.add_argument('-e', '--end',
                            dest='end',
                            help="End date.")

    args = arg_parser.parse_args()
    env_dir = os.getenv('DATASERVER_DIR')
    if not env_dir or not os.path.exists(env_dir) and not os.path.isdir(env_dir):
        raise IOError("Invalid dataserver environment root directory")

    conf_packages = ('nti.appserver',)
    context = create_context(env_dir, with_library=True)

    run_with_dataserver(environment_dir=env_dir,
                        verbose=args.verbose,
                        xmlconfig_packages=conf_packages,
                        context=context,
                        minimal_ds=True,
                        function=lambda: _process_args(args))
    sys.exit(0)


if __name__ == '__main__':
    main()
