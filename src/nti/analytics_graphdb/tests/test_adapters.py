#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from nti.dataserver.users import User

from nti.analytics_graphdb.tests import NTIAnalyticsGraphDBTestCase

class TestAdapters(NTIAnalyticsGraphDBTestCase):

	def create_user(self, username='nt@nti.com', password='temp001', **kwargs):
		usr = User.create_user(self.ds, username=username, password=password, **kwargs)
		return usr
