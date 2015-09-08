#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.async.redis_queue import RedisQueue

from nti.async.interfaces import IRedisQueue
from nti.async.interfaces import IAsyncReactor
from nti.async.interfaces import IReactorStarted

from nti.dataserver.interfaces import IRedisClient

from . import QUEUE_NAME

@component.adapter(IAsyncReactor, IReactorStarted)
def _reactor_started(reactor, event):
	if component.queryUtility(IRedisQueue, QUEUE_NAME) != None:
		return
	redis = component.getUtility(IRedisClient)
	queue = RedisQueue(redis, QUEUE_NAME)
	component.globalSiteManager.registerUtility(queue, IRedisQueue, QUEUE_NAME)
	reactor.add_queues(QUEUE_NAME)
