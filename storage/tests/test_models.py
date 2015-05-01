# encoding: utf-8

# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.
from django.core.exceptions import ValidationError

from django.test import TestCase

from storage import models


class TestBook(TestCase):
    def setUp(self):
        self.book = models.Book.objects.create(title='The Title')

    def test_book_has_unicode_method(self):
        """Book should have a __unicode__ method."""
        expected = u'Book "{}"'.format(self.book.title)
        self.assertEquals(expected, unicode(self.book))

    def test_book_unicode_handles_non_ascii(self):
        """Book __unicode__ should handle non-ascii."""
        self.book.title = u'El Título'
        expected = u'Book "El Título"'
        self.assertEquals(expected, unicode(self.book))

    def test_book_save_method_raises_error_on_title_overflow(self):
        """book.save() should raise an error if title exceeds max length"""
        self.book.title = 'X' * 1000
        with self.assertRaises(ValidationError):
            self.book.save()


class TestAlias(TestCase):
    def setUp(self):
        self.book = models.Book.objects.create(title=u'El Título')
        self.alias = models.Alias.objects.create(book_id=self.book.id, scheme='Foobar', value='42')

    def test_alias_has_unicode_method(self):
        """Alias should have a __unicode__ method."""
        alias = self.alias
        expected = u'"{}": {} / {}'.format(self.book.title, alias.scheme, alias.value)
        self.assertEquals(expected, unicode(alias))

    def test_alias_unicode_handles_non_ascii(self):
        """Alias __unicode__ should handle non-ascii."""
        self.alias.scheme = u'FØØ-12'
        self.alias.value = u'12345'
        expected = u'"{}": FØØ-12 / 12345'.format(self.book.title)
        self.assertEquals(expected, unicode(self.alias))

    def test_book_save_method_raises_error_on_scheme_overflow(self):
        """Alias.save() should raise an error if scheme exceeds max length"""
        self.alias.scheme = 'X' * 1000
        with self.assertRaises(ValidationError):
            self.alias.save()

    def test_book_save_method_raises_error_on_value_overflow(self):
        """Alias.save() should raise an error if value exceeds max length"""
        self.alias.value = 'X' * 1000
        with self.assertRaises(ValidationError):
            self.alias.save()
