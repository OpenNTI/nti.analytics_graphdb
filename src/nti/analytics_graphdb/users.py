#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.dataserver.interfaces import IUser
from nti.dataserver.users.interfaces import IWillDeleteEntityEvent

from .interfaces import IOID

from . import create_job
from . import get_job_queue
from . import get_predictionio_app
from . import get_predictionio_client

def _remove_user(app, username):
	client = get_predictionio_client(app=app)
	if client is not None:
		try:
			client.delete_user(username)
		finally:
			client.close()
		logger.debug("User '%s' was removed", username)

def _process_removal(app, user):
	userid = IOID(user)
	queue = get_job_queue()
	job = create_job(_remove_user, app=app, username=userid)
	queue.put(job)

@component.adapter(IUser, IWillDeleteEntityEvent)
def _user_removed(user, event):
	app = get_predictionio_app()
	if app is not None:
		_process_removal(app, user)
