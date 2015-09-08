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

from .utils import get_latlong
from .utils import create_user_event

from .interfaces import IOID

from . import VIEW_API
from . import primitives as primitives_types

from . import get_user
from . import create_job
from . import get_job_queue
from . import get_predictionio_app

def _process_view_event(app, username, oid, params=None, event_time=None):
	return create_user_event(event=VIEW_API,
			  		 	 	 user=username,
			  		 	 	 obj=oid,
			  		 	 	 app=app,
			  			 	 params=params,
			  			 	 event_time=event_time)

@component.adapter(IObjectViewedRecordedEvent)
def _object_viewed(event):
	app = get_predictionio_app()
	if app is None:
		return

	params = {}
	user = get_user(event.user)
	oid = IOID(event.object, None)
	sessionId = event.sessionId

	# latlong
	latlong = get_latlong(sessionId) if sessionId is not None else None
	if latlong:
		params["pio_latlng"] = ",".join(latlong)

	# handle context
	context = getattr(event, 'context', None)
	if not isinstance(context, primitives_types):
		context = IOID(context, None)
	if context is not None:
		params['context'] = str(context)

	# event time
	event_time = getattr(event, 'timestamp', None)

	# add event properties
	for name in ('duration', 'context_path', 'video_end_time',
			  	 'with_transcript', 'video_start_time'):
		value = getattr(event, name, None)
		if value is not None:
			params[name] = str(value)

	queue = get_job_queue()
	job = create_job(_process_view_event, app=app, username=user.username, oid=oid,
					 params=params, event_time=event_time)
	queue.put(job)
