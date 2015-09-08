#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import uuid
import shutil
import tempfile

import zope.testing.cleanup

from nti.testing.layers import find_test
from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

from nti.dataserver.tests.mock_dataserver import DSInjectorMixin

DEFAULT_URI = u'http://localhost:7474/db/data/'

def random_username():
    splits = unicode(uuid.uuid4()).split('-')
    username = "%s@%s" % (splits[-1], splits[0])
    return username

class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 GCLayerMixin,
                                 ConfiguringLayerMixin,
                                 DSInjectorMixin):

    set_up_packages = ('nti.analytics', 'nti.analytics_pio')

    @classmethod
    def setUp(cls):
        cls.setUpPackages()
        cls.old_data_dir = os.getenv('DATASERVER_DATA_DIR')
        cls.new_data_dir = tempfile.mkdtemp(dir="/tmp")
        os.environ['DATASERVER_DATA_DIR'] = cls.new_data_dir

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None):
        cls.setUpTestDS(test)
        shutil.rmtree(cls.new_data_dir, True)
        os.environ['DATASERVER_DATA_DIR'] = cls.old_data_dir or '/tmp'

    @classmethod
    def testTearDown(cls):
        pass

from nti.analytics.tests import NTIAnalyticsTestCase

class NTIAnalyticsPIOTestCase(NTIAnalyticsTestCase):
    layer = SharedConfiguringTestLayer
