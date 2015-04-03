# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 4:58 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.
from django.db import transaction

from storage.models import Alias, Book, Conflict


def process_book_element(book_element):
    """Process a book element into the database.

    Simple wrapper method that takes XML as input.
    """
    incoming = extract_book_data(book_element)
    book, update_type, num_conflicts = store_book_with_conflicts(incoming)
    return book, update_type, num_conflicts


def store_book_with_conflicts(incoming):
    """Given a dict of incoming data, persist a Book, its Aliases, and and any Conflicts

    We store the publisher id as another alias. If we have any alias conflicts (including pub_id)
    we create a Conflict object so we can research and fix the issue. Possible resolutions can
    include correcting the data or merging aliases/books to point to the canonical book.

    Since this takes an incoming dictionary, it could work just fine with the results of
    a form's cleaned_data output with similar structure.
    """
    found = Alias.objects.filter(scheme='PUB_ID', value=incoming['publisher_id'])
    num_found = found.count()
    if num_found == 1:
        book = found[0].book
        update_type = 'Updated'
    else:
        book = Book()
        update_type = 'Created'

    book = populate_and_save(book, incoming)
    conflicted_aliases = get_alias_conflicts(book)
    num_conflicts = create_conflicts(book, conflicted_aliases)
    return book, update_type, num_conflicts


def create_conflicts(book, dupe_aliases):
    """Create a Conflict object for each alias duplicate; return count of newly created Conflicts"""
    num_created = 0
    for alias in dupe_aliases:
        conflict, created = Conflict.objects.get_or_create(book=book, conflicted_alias=alias)
        num_created = num_created + 1 if created else num_created
    return num_created


def get_alias_conflicts(book):
    """Return a list of Aliases on other books that match the aliases on newly created Book"""
    conflicts = []
    for a in book.aliases.all():
        conflicts.append(Alias.objects.filter(scheme=a.scheme, value=a.value).exclude(book=book))

    # The call `conflicts.append(Alias.obj...` results in a list of QuerySets; flatten those out.
    flattened_conflicts = [item for found_set in conflicts for item in found_set]
    return flattened_conflicts


def populate_and_save(book, incoming):
    """Populate book object with values from incoming dict and save the Book/Aliases"""

    with transaction.atomic():
        book.title = incoming['title']
        book.description = incoming['description']
        book.save()
        for alias in incoming['aliases']:
            book.aliases.get_or_create(scheme=alias['scheme'], value=alias['value'])
        return book


def extract_book_data(book_element):
    """Return a dict of the data extracted from provided element

    Note that the publisher id is available as a key in the dict and also stored as an alias with
    a scheme of PUB_ID.

    The 'aliases' key will return a list of dicts with two keys: 'scheme' and 'value'
    """
    title = book_element.findtext('title', default='').strip()
    publisher_id = book_element.get('id', default='').strip()
    description = book_element.findtext('description', default='').strip()

    if not title:
        raise ValueError('No data in title element')
    if not publisher_id:
        raise ValueError('No data for publisher id')

    # Translate the publisher id into an alias, then add the other aliases
    aliases = [{'scheme': 'PUB_ID', 'value': publisher_id}]
    for alias in book_element.xpath('aliases/alias'):
        aliases.append({'scheme': alias.get('scheme'), 'value': alias.get('value')})

    return {
        'publisher_id': publisher_id,
        'title': title,
        'description': description,
        'aliases': aliases}
