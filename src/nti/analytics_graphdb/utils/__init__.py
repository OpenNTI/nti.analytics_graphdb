#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.security.interfaces import NoInteraction

from geoip import geolite2

from nti.analytics.sessions import get_nti_session_id

from nti.analytics.database.sessions import get_session_by_id

from nti.coremetadata.utils import current_principal

from nti.dataserver.interfaces import IUser

from nti.dataserver.users.users import User


def get_current_username():
    try:
        return current_principal(False).id
    except (NoInteraction, IndexError, AttributeError):
        return None


def get_user(user=None):
    user = get_current_username() if user is None else user
    if user is not None and not IUser.providedBy(user):
        user = User.get_user(str(user))
    return user
get_current_user = get_user


def get_latlong_by_ip(ip_addr=None):
    match = geolite2.lookup(ip_addr) if ip_addr else None
    if match is not None:
        result = match.location or ()
        return result
    return None


def get_latlong(session_id=None):
    sid = get_nti_session_id() if session_id is None else session_id
    session = get_session_by_id(sid) if sid else None
    ip_addr = getattr(session, 'ip_addr', None)
    result = get_latlong_by_ip(ip_addr)
    return result
