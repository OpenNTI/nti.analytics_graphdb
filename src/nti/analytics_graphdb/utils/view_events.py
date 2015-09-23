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
from isodate import ISO8601Error

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import between
from sqlalchemy.orm import aliased

from zope import component

from zope.intid import IIntIds

from nti.analytics.database.users import Users
from nti.analytics.database.sessions import Sessions
from nti.analytics.database.blogs import BlogsViewed
from nti.analytics.database.blogs import BlogsCreated
from nti.analytics.database.resources import Resources
from nti.analytics.database.boards import TopicsViewed
from nti.analytics.database.boards import TopicsCreated
from nti.analytics.database.resource_views import VideoEvents
from nti.analytics.database.profile_views import EntityProfileViews
from nti.analytics.database.resource_views import CourseResourceViews
from nti.analytics.database.profile_views import EntityProfileActivityViews
from nti.analytics.database.profile_views import EntityProfileMembershipViews

from nti.dataserver.interfaces import INote

from nti.graphdb import create_job
from nti.graphdb import get_job_queue
from nti.graphdb.common import get_ntiid

from nti.externalization.oids import to_external_ntiid_oid

from nti.ntiids.ntiids import find_object_with_ntiid

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
		try:
			value = isodate.parse_datetime(value)
		except (ISO8601Error, ValueError):
			value = isodate.parse_date(value)
			value = datetime.fromordinal(value.toordinal())
	return value

def get_object(oid):
	if isinstance(oid, (int, long)): 
		intids = component.getUtility(IIntIds)
		result = intids.queryObject(oid)
	elif isinstance(oid, six.string_types):
		result = find_object_with_ntiid(oid)
	else:
		result = None
	return result

def blog_viewed_data(db, start=None, end=None):
	start = to_datetime(start, 0)
	end = to_datetime(end, int(time.time()))
	query = db.session.query(BlogsViewed.session_id.label('session_id'),
							 Users.username.label('username'), 
							 BlogsCreated.blog_ds_id.label('ds_intid'),
							 BlogsViewed.time_length.label('duration'),
							 BlogsViewed.context_path.label('context_path'),
							 BlogsViewed.timestamp.label('timestamp')).\
					outerjoin((Sessions, Sessions.session_id == BlogsViewed.session_id)).\
					filter(BlogsViewed.blog_id==BlogsCreated.blog_id).\
					filter(BlogsViewed.user_id==Users.user_id).\
					filter(between(BlogsViewed.timestamp, start, end)).\
					filter(and_(BlogsViewed.time_length is not None, 
								BlogsViewed.time_length > 0)).distinct()
	return query

def topics_viewed_data(db, start=None, end=None):
	start = to_datetime(start, 0)
	end = to_datetime(end, int(time.time()))
	query = db.session.query(TopicsViewed.session_id.label('session_id'),
							 Users.username.label('username'), 
							 TopicsCreated.topic_ds_id.label('ds_intid'),
							 TopicsViewed.time_length.label('duration'),
							 TopicsViewed.context_path.label('context_path'),
							 TopicsViewed.timestamp.label('timestamp')).\
					outerjoin((Sessions, Sessions.session_id == TopicsViewed.session_id)).\
					filter(TopicsViewed.topic_id==TopicsCreated.topic_id).\
					filter(TopicsViewed.user_id==Users.user_id).\
					filter(between(TopicsViewed.timestamp, start, end)).\
					filter(and_(TopicsViewed.time_length is not None, 
								TopicsViewed.time_length > 0)).distinct()
	return query

def videos_viewed_data(db, start=None, end=None):
	start = to_datetime(start, 0)
	end = to_datetime(end, int(time.time()))
	query = db.session.query(VideoEvents.session_id.label('session_id'),
							 Users.username.label('username'), 
							 Resources.resource_ds_id.label('ds_intid'),
							 VideoEvents.time_length.label('duration'),
							 VideoEvents.context_path.label('context_path'),
							 VideoEvents.video_start_time.label('video_start_time'),
							 VideoEvents.video_end_time.label('video_end_time'),
							 VideoEvents.with_transcript.label('with_transcript'),
							 VideoEvents.timestamp.label('timestamp')).\
					outerjoin((Sessions, Sessions.session_id == VideoEvents.session_id)).\
					filter(VideoEvents.resource_id==Resources.resource_id).\
					filter(VideoEvents.user_id==Users.user_id).\
					filter(VideoEvents.video_event_type=='WATCH').\
					filter(between(VideoEvents.timestamp, start, end)).\
					filter(and_(VideoEvents.time_length is not None, 
								VideoEvents.time_length > 0)).distinct()
	return query

def course_resources_viewed_data(db, start=None, end=None):
	start = to_datetime(start, 0)
	end = to_datetime(end, int(time.time()))
	query = db.session.query(CourseResourceViews.session_id.label('session_id'),
							 Users.username.label('username'), 
							 Resources.resource_ds_id.label('ds_intid'),
							 CourseResourceViews.time_length.label('duration'),
							 CourseResourceViews.context_path.label('context_path'),
							 CourseResourceViews.timestamp.label('timestamp')).\
					outerjoin((Sessions, Sessions.session_id == CourseResourceViews.session_id)).\
					filter(CourseResourceViews.resource_id==Resources.resource_id).\
					filter(CourseResourceViews.user_id==Users.user_id).\
					filter(between(CourseResourceViews.timestamp, start, end)).distinct()
	return query

def profile_viewed_data(db, start=None, end=None):
	start = to_datetime(start, 0)
	end = to_datetime(end, int(time.time()))
	def _process(table, type_):
		users_alias = aliased(Users, name='users_alias')
		query = db.session.query(table.session_id.label('session_id'),
								 Users.username.label('username'), 
								 users_alias.user_ds_id.label('ds_intid'),
								 table.time_length.label('duration'),
								 table.context_path.label('context_path'),
								 table.timestamp.label('timestamp'),
								 func.concat(type_).label("type")).\
						outerjoin((Sessions, Sessions.session_id == table.session_id)).\
						filter(table.target_id==users_alias.user_id).\
						filter(table.user_id==Users.user_id).\
						filter(between(table.timestamp, start, end)).\
						filter(and_(table.time_length is not None, 
									table.time_length > 0)).distinct()
		return query
	
	profile = _process(EntityProfileViews, 'Profile')
	activity = _process(EntityProfileActivityViews, 'Activity')
	membership = _process(EntityProfileMembershipViews, 'Membership')
	result = membership.union(activity).union(profile)
	return result

def process_view_event(db, sessionId, username, oid, params):
	user = get_user(username) if username else None
	if user is None:
		return
	
	if isinstance(oid, (int, long)): 
		obj = get_object(oid)
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

	if 'event_time' in params:
		params['createdTime'] = params['event_time']

	queue = get_job_queue()
	job = create_job(add_view_relationship, db=db, username=user.username,
					 oid=oid, params=params)
	queue.put(job, use_transactions=False)
	return True
			
def populate_graph_db(gdb, analytics, start=None, end=None):
	result = 0
	
	logger.info("Populating view events")

	blogs_viewed = blog_viewed_data(analytics, start, end)
	topics_views = topics_viewed_data(analytics, start, end)
	for row in topics_views.union(blogs_viewed):
		__traceback_info__ = row
		sessionId, username, oid, duration = row[:4]
		if not duration:
			continue
		
		params = {'duration': duration,
				  'event_time':time.mktime(row[5].timetuple()) }
		if row[4]:
			params['context_path'] = row[4]

		if process_view_event(gdb, sessionId, username, oid, params):
			result += 1
	logger.info("%s blog and topic event(s) processed", result)
	
	count = 0
	for row in course_resources_viewed_data(analytics, start, end):
		__traceback_info__ = row
		sessionId, username, oid, duration = row[:4]
		obj = get_object(oid)
		if obj is None:
			continue
		if not duration and not INote.providedBy(obj):
			continue

		if not isinstance(oid, six.string_types):
			oid = get_ntiid(obj) or to_external_ntiid_oid(obj)

		params = {'duration': duration or 1,
				  'event_time':time.mktime(row[5].timetuple()) }
		if row[4]:
			params['context_path'] = row[4]

		if process_view_event(gdb, sessionId, username, oid, params):
			count += 1

	result += count
	logger.info("%s course resource view event(s) processed", count)
	
	count = 0
	for row in videos_viewed_data(analytics, start, end):
		__traceback_info__ = row
		sessionId, username, oid, duration = row[:4]
		params = {'duration': duration,
				  'event_time':time.mktime(row[8].timetuple()) }
		if row[4]:
			params['context_path'] = row[4]
		if row[5]:
			params['video_start_time'] = row[5]
		if row[6]:
			params['video_end_time'] = row[6]
		params['with_transcript'] = row[7] or False
		
		if process_view_event(gdb, sessionId, username, oid, params):
			count += 1
			
	result += count
	logger.info("%s video view event(s) processed", count)

	count = 0
	for row in profile_viewed_data(analytics, start, end):
		__traceback_info__ = row
		sessionId, username, oid, duration = row[:4]
		params = {'duration': duration,
				  'event_time':time.mktime(row[5].timetuple()) }
		if row[4]:
			params['context_path'] = row[4]
		if row[6]:
			params['profile_view_type'] = row[6]
		
		if process_view_event(gdb, sessionId, username, oid, params):
			count += 1
	
	result += count
	logger.info("%s profile view event(s) processed", count)
		
	return result
