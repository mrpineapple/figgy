# encoding: utf-8

# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

import uuid

from django.test import TestCase

from storage import models


class TestModels(TestCase):
    def setUp(self):
        self.book = models.Book.objects.create(title='The Title', pk=str(uuid.uuid4()))

    def test_book_has_unicode_method(self):
        """Book should have a __unicode__ method."""
        expected = u'Book {0}'.format(self.book.title)
        self.assertEquals(expected, unicode(self.book))

    def test_book_unicode_handles_non_ascii(self):
        """Book __unicode__ should handle non-ascii."""
        self.book.title = u'El Título'
        expected = u'Book El Título'
        self.assertEquals(expected, unicode(self.book))


class TestAlias(TestCase):
    def setUp(self):
        self.book = models.Book.objects.create(title=u'El Título', pk=str(uuid.uuid4()))
        self.alias = models.Alias.objects.create(book_id=self.book.id, scheme='Foobar', value='42')

    def test_alias_has_unicode_method(self):
        """Alias should have a __unicode__ method."""
        expected = u'{0} identifier for {1}'.format(self.alias.scheme, self.book.title)
        self.assertEquals(expected, unicode(self.alias))

    def test_alias_unicode_handles_non_ascii(self):
        """Alias __unicode__ should handle non-ascii."""
        self.alias.scheme = u'FØØ-12'
        expected = u'FØØ-12 identifier for {0}'.format(self.book.title)
        self.assertEquals(expected, unicode(self.alias))