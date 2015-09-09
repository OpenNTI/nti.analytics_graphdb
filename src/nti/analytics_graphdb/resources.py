#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import component

from nti.analytics.recorded import IVideoRecordedEvent
from nti.analytics.recorded import IVideoSkipRecordedEvent
from nti.analytics.recorded import IObjectViewedRecordedEvent

from nti.graphdb import create_job
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue
from nti.graphdb.common import get_ntiid
from nti.graphdb.relationships import Viewed

from nti.externalization.oids import to_external_ntiid_oid

from nti.ntiids.ntiids import find_object_with_ntiid

from .utils import get_user
from .utils import get_latlong

from . import primitives_types

def _add_view_relationship(db, oid, username, params=None):
	params = params or {}
	user = get_user(username)
	obj = find_object_with_ntiid(oid)
	if user is not None and obj is not None:
		result = db.create_relationship(user, obj, Viewed(),
										unique=False, properties=params)
		logger.debug("Viewed relationship %s created", result)

def _process_view_event(db, event):
	if IVideoRecordedEvent.providedBy(event) and event.duration <= 0: # skip 0 events
		return
	params = {}
	obj = event.object
	user = get_user(event.user)
	sessionId = event.sessionId
	if isinstance(obj, six.string_types): # ntiid
		oid = obj
	else:
		oid = get_ntiid(obj) or to_external_ntiid_oid(event.object)
		
	if oid is None:
		logger.warn("Could not get OID for event %s", event)
		return

	# latlong
	latlong = get_latlong(sessionId) if sessionId is not None else None
	if latlong:
		params["latlong"] = ",".join(latlong)

	# context
	context = getattr(event, 'context', None)
	if not isinstance(context, primitives_types):
		context = to_external_ntiid_oid(context) if context is not None else None
	if context is not None:
		params['context'] = str(context)

	# event time
	event_time = getattr(event, 'timestamp', None)
	if event_time:
		params['event_time'] = event_time

	# event properties
	for name in ('duration', 'context_path', 'video_end_time',
				 'with_transcript', 'video_start_time'):
		value = getattr(event, name, None)
		if value is not None:
			params[name] = str(value)

	queue = get_job_queue()
	job = create_job(_add_view_relationship, db=db, username=user.username,
					 oid=oid, params=params)
	queue.put(job)

@component.adapter(IObjectViewedRecordedEvent)
def _object_viewed(event):
	db = get_graph_db()
	if db is not None and not IVideoSkipRecordedEvent.providedBy(event):
		_process_view_event(db, event)
