# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 5:01 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

from lxml import etree

from django.test import TestCase

from storage.models import Book, Alias, Conflict, UpdateFile
import storage.tools as tools


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
        self.hash = 'A' * 40

    def test_storage_tools_process_book_element_db(self):
        """process_book_element should put the book in the database."""
        xml = etree.fromstring(self.xml_str)
        tools.process_book_element(xml, 'filename', self.hash)

        self.assertEqual(Book.objects.count(), 1)
        book = Book.objects.get(title=u'El Título')

        self.assertEqual(book.title, u'El Título')
        self.assertEqual(book.aliases.count(), 3)
        self.assertEqual(Alias.objects.get(scheme='ISBN-10').value, '0158757819')
        self.assertEqual(Alias.objects.get(scheme='ISBN-13').value, '0000000000123')
        self.assertEqual(Alias.objects.get(scheme='PUB_ID').value, '12345')

    def test_storage_tools_reprocess_same_file(self):
        """process_book_element should not reprocess an identical file"""
        xml = etree.fromstring(self.xml_str)
        tools.process_book_element(xml, 'filename', self.hash)
        self.assertEqual(Book.objects.count(), 1)

        book = Book.objects.get(title=u'El Título')
        self.assertEqual(book.aliases.count(), 3)
        self.assertEqual(Conflict.objects.count(), 0)
        self.assertEqual(UpdateFile.objects.count(), 1)

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
        bogus_hash = '2' * 40
        tools.process_book_element(xml, 'filename2', bogus_hash)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(Alias.objects.count(), 6)
        self.assertEqual(Conflict.objects.count(), 2)
        self.assertEqual(UpdateFile.objects.count(), 2)

        # ... DO NOT process it again, even if we try
        tools.process_book_element(xml, 'filename2', bogus_hash)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(Alias.objects.count(), 6)
        self.assertEqual(Conflict.objects.count(), 2)
        self.assertEqual(UpdateFile.objects.count(), 2)


class TestSupportingTools(TestCase):

    def test_hash_file(self):
        """hash_file should return a git compatible SHA1"""
        # To get expected sha1 value (be sure to use -e):
        # $ echo -e foobar\n | git hash-object --stdin

        expected = 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391'
        self.assertEqual(tools.hash_data(''), expected)

        expected = '323fae03f4606ea9991df8befbb2fca795e648fa'
        self.assertEqual(tools.hash_data('foobar\n'), expected)

    def test_populate_book_attrs(self):
        """populate_book_attrs should populate Book attrs with incoming and return pub_id alias"""
        book = Book.objects.create()
        aliases = {'aliases': [
            {'scheme': 'PUB_ID', 'value': '123'},
            {'scheme': 'FOO', 'value': 'BAR'}
        ]}
        incoming = {
            'publisher_id': '123',
            'title': 'The Title',
            'description': 'Exciting new book',
            'aliases': aliases
        }

        incoming.update(aliases)
        book, pub_id_alias = tools.populate_book_attrs(book, incoming)
        self.assertEqual(book.title, incoming['title'])
        self.assertEqual(book.description, incoming['description'])
        self.assertEqual(pub_id_alias.scheme, 'PUB_ID')
        self.assertEqual(pub_id_alias.value, '123')
        book.save()
        aliases = Alias.objects.filter(book=book)
        self.assertEqual(len(aliases), 2)

    def test_parse_book_element(self):
        """parse_book_element should parse XML data into dict of appropriate values"""
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
        data = tools.parse_book_element(book_element)
        self.assertEqual(data['publisher_id'], '123')
        self.assertEqual(data['title'], 'The Title')
        self.assertEqual(data['description'], 'The desc')
        self.assertEqual(data['aliases'], [
            {'scheme': 'THIS', 'value': 'THAT'},
            {'scheme': 'FOO', 'value': 'BAR'},
        ])


class TestProcessingConflicts(TestCase):

    def setUp(self):
        existing_book = Book.objects.create(title='The Title')
        existing_book.aliases.create(scheme='PUB_ID', value='123')
        existing_book.aliases.create(scheme='THIS', value='THAT')
        existing_book.aliases.create(scheme='FOO', value='BAR')
        existing_book.save()
        self.existing_book = existing_book

    def test_get_alias_conflicts_one_existing_alias(self):
        """get_alias_conflicts should return a list of Alias conflict with book.aliases"""

        new_book = Book.objects.create(title='Ninjas are For Movies')
        incoming_aliases = [
            {'scheme': 'THIS', 'value': 'THAT'},
        ]
        conflicts = tools.get_alias_conflicts(new_book, incoming_aliases)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].scheme, 'THIS')
        self.assertEqual(conflicts[0].value, 'THAT')

    def test_get_alias_conflicts_ignores_itself(self):
        """get_alias_conflicts should return an empty list if no new conflicts in incoming data"""
        new_book = Book.objects.get(title='The Title')
        incoming_aliases = [
            {'scheme': 'THIS', 'value': 'THAT'},
        ]
        conflicts = tools.get_alias_conflicts(new_book, incoming_aliases)
        self.assertEqual(conflicts, [])
