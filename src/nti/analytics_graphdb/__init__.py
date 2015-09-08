#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import numbers

from zope import component
from zope.security.management import queryInteraction

from predictionio import EventClient

from nti.async import create_job

from nti.dataserver.users import User
from nti.dataserver.interfaces import IUser

from nti.analytics import get_factory

from nti.ntiids.ntiids import find_object_with_ntiid

from .interfaces import IPredictionIOApp

VIEW_API = "view"
LIKE_API = "like"
DISLIKE_API = "dislike"
LIKE_CAT_NAME = "likes"
RATE_CATE_NAME = 'rating'

QUEUE_NAME = "++etc++analytics_pio++queue"

primitives = six.string_types + (numbers.Number, bool)

def get_predictionio_app(name=''):
	result = component.getUtility(IPredictionIOApp, name=name)
	return result

def get_predictionio_client(client=None, app=None, name=''):
	if client is None:
		app = get_predictionio_app(name=name) if app is None else app
		if app is not None:
			access_key = str(app.AppKey)
			client = EventClient(access_key=access_key, url=app.URL)
	return client

def get_job_queue(name=QUEUE_NAME):
	return get_factory().get_queue(name)

def get_current_username():
	interaction = queryInteraction()
	participations = list(getattr(interaction, 'participations', None) or ())
	participation = participations[0] if participations else None
	principal = getattr(participation, 'principal', None)
	result = principal.id if principal is not None else None
	return result

def get_user(user=None):
	user = get_current_username() if user is None else user
	if user is not None and not IUser.providedBy(user):
		user = User.get_user(str(user))
	return user
get_current_user = get_user

def object_finder(obj):
	if isinstance(obj, six.string_types):
		return find_object_with_ntiid(obj)
	return obj
find_object = object_finder
