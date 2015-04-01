# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 4:58 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

from storage.models import Alias, Book, Conflict


def process_book_element(book_element):
    """Process a book element into the database.

    We store the published id as another aliases. If we have any alias conflicts (including pub_id)
    we create a Conflict object so we can research and fix the issue. Possible resolutions can
    include correcting the data or merging aliases to point to the canonical book.
    """
    incoming = parse_book_element(book_element)
    found = Alias.objects.filter(value=incoming['publisher_id'])
    num_found = len(found)

    book = found[0].book if num_found == 1 else Book.objects.create()
    book, pub_id_alias = populate_book_attrs(book, incoming)
    book.save()

    conflicted_aliases = get_alias_conflicts(book, incoming['aliases'])
    conflicted_aliases = conflicted_aliases + list(found) if num_found > 1 else conflicted_aliases
    num_conflicts = create_conflicts(book, set(conflicted_aliases))
    return book.title, num_conflicts


def create_conflicts(book, alias_set):
    """Create a Conflict object for each alias duplicate; return number created"""
    created = 0
    for alias in alias_set:
        conflict, created = Conflict.objects.get_or_create(book=book, conflicted_alias=alias)
        conflict.description = '[Auto] created on import'
        conflict.save()
        created += 1
    return created


def get_alias_conflicts(book, aliases):
    """Return a list of Alias records match the alias data provided by incoming book"""
    conflicts = []
    for incoming_alias in aliases:
        scheme = incoming_alias['scheme']
        value = incoming_alias['value']
        conflicts.append(Alias.objects.filter(scheme=scheme, value=value).exclude(book=book))
    # Filtering means we get back a list of zero or more possible aliases, flatten that
    flattened_conflicts = [item for found_set in conflicts for item in found_set]
    return flattened_conflicts


def parse_book_element(book_element):
    """Parse the book data, return a dictionary of values"""
    publisher_id = book_element.get('id')
    title = book_element.findtext('title')    
    description = book_element.findtext('description')

    aliases = []
    for alias in book_element.xpath('aliases/alias'):
        aliases.append({'scheme': alias.get('scheme'), 'value': alias.get('value')})

    return {
        'publisher_id': publisher_id,
        'title': title,
        'description': description,
        'aliases': aliases}
    

def populate_book_attrs(book, incoming):
    """Populate book object with values from incoming dict, including an alias for publisher id"""
    book.title = incoming['title']
    book.description = incoming['description']
    for alias in incoming['aliases']:
        book.aliases.get_or_create(scheme=alias['scheme'], value=alias['value'])
    alias, created = book.aliases.get_or_create(scheme='PUB_ID', value=incoming['publisher_id'])
    return book, alias
