#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.analytics.recorded import IObjectViewedRecordedEvent

from nti.graphdb import create_job
from nti.graphdb import get_job_queue

from .utils import get_user
from .utils import get_latlong

def _process_view_event(app, username, oid, params=None, event_time=None):
	pass

@component.adapter(IObjectViewedRecordedEvent)
def _object_viewed(event):
	params = {}
	oid = None
	user = get_user(event.user)
	sessionId = event.sessionId
#
	# latlong
	latlong = get_latlong(sessionId) if sessionId is not None else None
	if latlong:
		params["pio_latlng"] = ",".join(latlong)
#
#	 # handle context
#	 context = getattr(event, 'context', None)
#	 if not isinstance(context, primitives_types):
#		 context = IOID(context, None)
#	 if context is not None:
#		 params['context'] = str(context)

	# event time
	event_time = getattr(event, 'timestamp', None)

	# add event properties
	for name in ('duration', 'context_path', 'video_end_time',
				   'with_transcript', 'video_start_time'):
		value = getattr(event, name, None)
		if value is not None:
			params[name] = str(value)

	queue = get_job_queue()
	job = create_job(_process_view_event, username=user.username, oid=oid,
					 params=params, event_time=event_time)
	queue.put(job)
