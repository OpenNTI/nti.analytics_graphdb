#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from contentratings.interfaces import IObjectRatedEvent

from nti.dataserver.interfaces import IRatable
from nti.dataserver.rating import IObjectUnratedEvent

from .interfaces import IOID

from .utils import get_latlong
from .utils import create_user_event

from . import LIKE_API
from . import DISLIKE_API
from . import LIKE_CAT_NAME
from . import RATE_CATE_NAME

from . import create_job
from . import get_job_queue
from . import get_predictionio_app
from . import get_current_username

def _process_like_pio(app, username, oid, api, params=None):
	return create_user_event(event=api,
				  		 	 user=username,
				  		 	 obj=oid,
				  			 params=params,
				  			 app=app)

def _record_like(app, username, oid, params=None):
	_process_like_pio(app, username, oid, LIKE_API, params=params)

def _record_unlike(app, username, oid, params=None):
	_process_like_pio(app, username, oid, DISLIKE_API, params=params)

def _process_like_event(app, username, oid, like=True, latlong=None):
	params = {"pio_latlng": ",".join(latlong)} if latlong else None
	queue = get_job_queue()
	if like:
		job = create_job(_record_like, app=app, username=username, oid=oid,
					 	 params=params)
	else:
		job = create_job(_record_unlike, app=app, username=username, oid=oid,
					 	 params=params)
	queue.put(job)

def _record_rating(app, username, oid, rating, latlong=None, params=None):
	params = params or {}
	params['pio_rate'] = int(rating)
	if latlong:
		params["pio_latlng"] = ",".join(latlong)

	result = create_user_event(event="rate",
			  		 		   user=username,
			  		 		   obj=oid,
			  			 	   params=params,
			  			 	   app=app)
	return result

def _process_rating_event(app, username, oid, rating, latlng=None):
	queue = get_job_queue()
	job = create_job(_record_rating, app=app, username=username, rating=rating,
					 oid=oid, latlng=latlng)
	queue.put(job)

@component.adapter(IRatable, IObjectRatedEvent)
def _object_rated(modeled, event):
	app = get_predictionio_app()
	username = get_current_username()
	if username and app:
		oid = IOID(modeled)
		latlong = get_latlong()
		if event.category == LIKE_CAT_NAME:
			like = event.rating != 0
			_process_like_event(app, username, oid, like, latlong=latlong)
		elif event.category == RATE_CATE_NAME and \
			 not IObjectUnratedEvent.providedBy(event):
			rating = getattr(event, 'rating', None)
			_process_rating_event(app, username, oid, rating, latlong=latlong)
