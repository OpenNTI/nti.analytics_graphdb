#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import time
from datetime import datetime

import isodate

from sqlalchemy import between

from zope import component

from zope.intid import IIntIds

from nti.analytics.database.users import Users

from nti.analytics.database.blogs import BlogsViewed
from nti.analytics.database.blogs import BlogsCreated

from nti.analytics.database.sessions import Sessions

from nti.graphdb import create_job
from nti.graphdb import get_job_queue
from nti.graphdb.common import get_ntiid

from nti.externalization.oids import to_external_ntiid_oid

from ..resources import add_view_relationship

from . import get_user
from . import get_latlong

def to_datetime(value, default=None):
	value = default if value is None else value
	if value is None:
		return None
	elif isinstance(value, (int,float)):
		value = datetime.fromtimestamp(value)
	elif isinstance(value, six.string_types):
		value = isodate.parse_datetime(value)
	return value

def blog_viewed_data(db, start=None, end=None):
	start = to_datetime(start, 0)
	end = to_datetime(end, int(time.time()))
	query = db.session.query(BlogsViewed.session_id.label('session_id'),
							 Users.username.label('username'), 
							 BlogsCreated.blog_ds_id.label('blog_ds_id'),
							 BlogsViewed.time_length.label('duration'),
							 BlogsViewed.context_path.label('context_path'),
							 BlogsViewed.timestamp.label('timestamp')).\
					outerjoin((Sessions, Sessions.session_id == BlogsViewed.session_id)).\
					filter(BlogsViewed.blog_id==BlogsCreated.blog_id).\
					filter(BlogsViewed.user_id==Users.user_id).\
					filter(between(BlogsViewed.timestamp, start, end))
	return query

def process_view_event(db, sessionId, username, oid, params):
	user = get_user(username) if username else None
	if user is None:
		return
	
	if isinstance(oid, (int, long)): 
		intids = component.getUtility(IIntIds)
		obj = intids.queryObject(oid)
		if obj is not None:
			oid = get_ntiid(obj) or to_external_ntiid_oid(obj)
		else:
			oid = None

	if oid is None:
		return

	params = {} if params is None else params
	latlong = get_latlong(sessionId) if sessionId is not None else None
	if latlong:
		params["latlong"] = ",".join(latlong)

	# event time
	event_time = params.pop('timestamp', None)
	if event_time:
		params['event_time'] = event_time

	queue = get_job_queue()
	job = create_job(add_view_relationship, db=db, username=user.username,
					 oid=oid, params=params)
	queue.put(job)
	return True
			
def populate_graph_db(gdb, analytics, start=None, end=None):
	result = 0
	for row in blog_viewed_data(analytics, start, end):
		sessionId, username, oid, duration = row[:4]
		if not duration:
			continue
		
		params = {'duration': duration,
				  'event_time':time.mktime(row[5].timetuple()) }
		if row[4]:
			params['context_path'] = row[4]

		if process_view_event(gdb, sessionId, username, oid, params):
			result += 1
	return result
