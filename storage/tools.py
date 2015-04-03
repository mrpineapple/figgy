# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 4:58 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

import hashlib

from storage.models import Alias, Book, Conflict, UpdateFile


def process_book_element(book_element, filename, sha1):
    """Process a book element into the database.

    We store the publisher id as another alias. If we have any alias conflicts (including pub_id)
    we create a Conflict object so we can research and fix the issue. Possible resolutions can
    include correcting the data or merging aliases/books to point to the canonical book.

    We store a hash of each file we process. We exit early if we have seen this file before.
    """

    updated_already = UpdateFile.objects.filter(sha1=sha1)
    if updated_already:
        update_file = updated_already[0]
        prev_filename = update_file.filename
        created_str = update_file.created_time.strftime('%c')
        return '{0} processed on {1} contained same data'.format(prev_filename, created_str)
    incoming = extract_book_data(book_element)

    found = Alias.objects.filter(scheme='PUB_ID', value=incoming['publisher_id'])
    num_found = found.count()

    book = found[0].book if num_found == 1 else Book()
    book = populate_and_save(book, incoming)

    conflicted_aliases = get_alias_conflicts(book)
    num_conflicts = create_conflicts(book, conflicted_aliases)

    msg = ''
    if num_conflicts:
        msg = 'created with {0} conflicts'.format(num_conflicts)
    UpdateFile.objects.create(filename=filename, sha1=sha1)
    return msg


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


def extract_book_data(book_element):
    """Return a dict of the data extracted from provided element

    Note that the publisher id is available as a key in the dict and also stored as an alias with
    a scheme of PUB_ID.

    The 'aliases' key will return a list of dicts with two keys: 'scheme' and 'value'
    """
    publisher_id = book_element.get('id')
    title = book_element.findtext('title')
    description = book_element.findtext('description')

    # Translate the publisher id into an alias, then add the other aliases
    aliases = [{'scheme': 'PUB_ID', 'value': publisher_id}]
    for alias in book_element.xpath('aliases/alias'):
        aliases.append({'scheme': alias.get('scheme'), 'value': alias.get('value')})

    return {
        'publisher_id': publisher_id,
        'title': title,
        'description': description,
        'aliases': aliases}
    

def populate_and_save(book, incoming):
    """Populate book object with values from incoming dict and save the Book/Aliases"""

    # NOTE: SQLite does not honor max_length of CharField ... I'm assuming we'd use a different
    # database in production, so I'm ignoring issues related to CharField overflow. Perhaps we
    # could override the various model save() methods to call full_clean() and have it throw
    # a DatabaseError (instead of ValidationError).

    book.title = incoming['title']
    book.description = incoming['description']
    book.save()
    for alias in incoming['aliases']:
        book.aliases.get_or_create(scheme=alias['scheme'], value=alias['value'])
    return book


def hash_data(contents):
    """Return a git-compatible sha1 hash for data, usually contents of file

    Using git-compatible hash since we may have the data files stored in git. Could be handy.
    If we get out of sync with the git format reason it shouldn't kill us.

    This is simple enough that it makes sense to implement here, rather than spawning a new process
    to use the git binary.
    """
    data = contents
    len_data = len(data)
    sha1 = hashlib.sha1()
    sha1.update('blob {0}\0'.format(len_data))
    sha1.update(contents)
    return sha1.hexdigest()