# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 5:01 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

from lxml import etree

from django.test import TestCase

from storage import tools
from storage.models import Book, Alias, Conflict


class TestProcessBookElement(TestCase):
    def setUp(self):
        self.xml_str = u"""
        <book id="12345">
            <title>El Título</title>
            <aliases>
                <alias scheme="ISBN-10" value="0158757819"/>
                <alias scheme="ISBN-13" value="0000000000123"/>
            </aliases>
        </book>
        """

    def test_storage_tools_process_book_element_db(self):
        """process_book_element should put the book in the database."""
        xml = etree.fromstring(self.xml_str)
        tools.process_book_element(xml)

        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.get(title=u'El Título')

        self.assertEqual(book.title, u'El Título')
        self.assertEqual(book.aliases.count(), 3)
        self.assertEqual(Alias.objects.get(scheme='ISBN-10').value, '0158757819')
        self.assertEqual(Alias.objects.get(scheme='ISBN-13').value, '0000000000123')
        self.assertEqual(Alias.objects.get(scheme='PUB_ID').value, '12345')

    def test_storage_tools_do_not_reprocess_same_file(self):
        """process_book_element should not reprocess an identical file"""
        xml = etree.fromstring(self.xml_str)
        tools.process_book_element(xml)
        self.assertEqual(Book.objects.count(), 1)

        book = Book.objects.get(title=u'El Título')
        self.assertEqual(book.aliases.count(), 3)
        self.assertEqual(Conflict.objects.count(), 0)

        # process an update that will generate new book, aliases and conflicts
        xml_update_str = u"""
        <book id="789">
            <title>El Título, 2e</title>
            <aliases>
                <alias scheme="ISBN-10" value="0158757819"/>
                <alias scheme="ISBN-13" value="0000000000123"/>
            </aliases>
        </book>
        """
        xml = etree.fromstring(xml_update_str)
        tools.process_book_element(xml)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(Alias.objects.count(), 6)
        self.assertEqual(Conflict.objects.count(), 2)

        # ... DO NOT process it again, even if we try
        tools.process_book_element(xml)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(Alias.objects.count(), 6)
        self.assertEqual(Conflict.objects.count(), 2)

    def test_storage_tools_populate_and_save(self):
        """populate_and_save should populate Book/Aliases with incoming data"""
        book = Book()
        incoming = {
            'publisher_id': '123',
            'title': 'The Title',
            'description': 'Exciting new book',
            'aliases': [
                {'scheme': 'PUB_ID', 'value': '123'},
                {'scheme': 'FOO', 'value': 'BAR'},
                {'scheme': 'THIS', 'value': 'THAT'}
            ]
        }

        book = tools.populate_and_save(book, incoming)
        self.assertTrue(isinstance(book.id, int))
        self.assertEqual(book.title, incoming['title'])
        self.assertEqual(book.description, incoming['description'])
        self.assertEqual(Alias.objects.count(), 3)
        self.assertEqual(Alias.objects.get(scheme='PUB_ID').value, '123')
        self.assertEqual(Alias.objects.get(scheme='FOO').value, 'BAR')
        self.assertEqual(Alias.objects.get(scheme='THIS').value, 'THAT')

    def test_storage_tools_extract_book_data(self):
        """extract_book_data should extract data from XML into dict of appropriate values"""
        book_element_str = """
        <book id="123">
            <title>The Title</title>
            <description>The desc</description>
            <aliases>
                <alias scheme="THIS" value="THAT"/>
                <alias scheme="FOO" value="BAR"/>
            </aliases>
        </book>
        """
        book_element = etree.fromstring(book_element_str)
        data = tools.extract_book_data(book_element)
        self.assertEqual(data['publisher_id'], '123')
        self.assertEqual(data['title'], 'The Title')
        self.assertEqual(data['description'], 'The desc')
        self.assertEqual(data['aliases'], [
            {'scheme': 'PUB_ID', 'value': '123'},
            {'scheme': 'THIS', 'value': 'THAT'},
            {'scheme': 'FOO', 'value': 'BAR'},
        ])


class TestProcessingConflicts(TestCase):

    def setUp(self):
        existing_book = Book.objects.create(title='The Title')
        existing_book.aliases.create(scheme='PUB_ID', value='123')
        existing_book.aliases.create(scheme='THIS', value='THAT')
        existing_book.aliases.create(scheme='FOO', value='BAR')
        self.existing_book = existing_book

    def test_storage_tools_get_alias_conflicts_one_existing_alias(self):
        """get_alias_conflicts should return a list of Alias conflict with book.aliases"""
        new_book = Book.objects.create(title='Ninjas are for Movies')
        new_book.aliases.create(scheme='THIS', value='THAT')
        conflicts = tools.get_alias_conflicts(new_book)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].scheme, 'THIS')
        self.assertEqual(conflicts[0].value, 'THAT')

    def test_storage_tools_get_alias_conflicts_ignores_itself(self):
        """get_alias_conflicts should return empty list if incoming data has no conflicts"""
        conflicts = tools.get_alias_conflicts(self.existing_book)
        self.assertEqual(conflicts, [])
