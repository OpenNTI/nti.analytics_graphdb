#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from nti.dataserver.interfaces import ICreated

from nti.dataserver.contenttypes.forums.interfaces import ITopic

from .interfaces import IOID

from . import create_job
from . import get_job_queue
from . import get_predictionio_app
from . import get_predictionio_client

def _remove_generated(app, oid):
	client = get_predictionio_client(app=app)
	if client is not None:
		try:
			client.delete_item(oid)
		finally:
			client.close()
		logger.debug("item '%s' was removed", oid)

def _process_removal(app, obj):
	queue = get_job_queue()
	job = create_job(_remove_generated, app=app, oid=IOID(obj))
	queue.put(job)

@component.adapter(ICreated, IObjectRemovedEvent)
def _created_removed(modeled, event):
	app = get_predictionio_app()
	if app is not None:
		_process_removal(app, modeled)

@component.adapter(ITopic, IObjectRemovedEvent)
def _topic_removed(topic, event):
	app = get_predictionio_app()
	if app is not None:
		_process_removal(app, topic)
