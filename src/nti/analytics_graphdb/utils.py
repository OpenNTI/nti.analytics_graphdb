#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.security.management import queryInteraction

from geoip import geolite2

from nti.analytics.identifier import SessionId
from nti.analytics.sessions import get_nti_session_id
from nti.analytics.database.sessions import get_session_by_id

from nti.dataserver.users import User
from nti.dataserver.interfaces import IUser

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

def get_latlong(nti_session=None):
	nti_session = get_nti_session_id() if nti_session is None else nti_session
	sid = SessionId.get_id(nti_session)
	session = get_session_by_id(sid) if sid else None
	ip_addr = getattr(session, 'ip_addr', None)
	match = geolite2.lookup(ip_addr) if ip_addr else None
	if match is not None:
		result = match.location or ()
		return result
	return None
