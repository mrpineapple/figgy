# encoding: utf-8

# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

from django.test import TestCase

from storage import models, tools


class TestModels(TestCase):
    def setUp(self):
        self.book = models.Book.objects.create(title='The Title', pk=42)

    def test_book_has_unicode_method(self):
        """Book should have a __unicode__ method."""
        expected = u'Book "{0}"'.format(self.book.title)
        self.assertEquals(expected, unicode(self.book))

    def test_book_unicode_handles_non_ascii(self):
        """Book __unicode__ should handle non-ascii."""
        self.book.title = u'El Título'
        expected = u'Book "El Título"'
        self.assertEquals(expected, unicode(self.book))


class TestAlias(TestCase):
    def setUp(self):
        self.book = models.Book.objects.create(title=u'El Título', pk=42)
        self.alias = models.Alias.objects.create(book_id=self.book.id, scheme='Foobar', value='42')

    def test_alias_has_unicode_method(self):
        """Alias should have a __unicode__ method."""
        alias = self.alias
        expected = u'"{0}": {1}/{2}'.format(self.book.title, alias.scheme, alias.value)
        self.assertEquals(expected, unicode(alias))

    def test_alias_unicode_handles_non_ascii(self):
        """Alias __unicode__ should handle non-ascii."""
        self.alias.scheme = u'FØØ-12'
        self.alias.value = u'12345'
        expected = u'"{0}": FØØ-12/12345'.format(self.book.title)
        self.assertEquals(expected, unicode(self.alias))


class TestUpdateFile(TestCase):

    def setUp(self):
        sha1 = tools.hash_data('foobar')
        self.update_file = models.UpdateFile.objects.create(filename='update-1.xml', sha1=sha1)

    def test_alias_has_unicode_method(self):
        """UpdateFile should have a __unicode__ method."""
        expected = u'{0}'.format(self.update_file.filename)
        self.assertEquals(expected, unicode(self.update_file))

    def test_alias_unicode_handles_non_ascii(self):
        """UpdateFile __unicode__ should handle non-ascii."""
        self.update_file.filename = u'üpdate-1.xml'
        expected = u'{0}'.format(self.update_file.filename)
        self.assertEquals(expected, unicode(self.update_file))
