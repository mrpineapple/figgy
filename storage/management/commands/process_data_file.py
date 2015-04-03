# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 4:56 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

from lxml import etree

from django.core.management.base import BaseCommand
from django.template.defaultfilters import pluralize

import storage.tools as tools


class Command(BaseCommand):
    args = '<filename filename2 filename3 ...>'
    help = 'Process an xml file '

    def handle(self, *args, **options):
        errors = []
        print('Processing {} titles\n'.format(len(args)))
        for filename in args:
            with open(filename, 'rb') as fh:
                print('Importing {} into database.'.format(filename))
                try:
                    book_node = etree.parse(fh).getroot()
                    book, update_type, conflicts = tools.process_book_element(book_node)
                    print('... {action} "{title}"'.format(action=update_type, title=book.title))
                    if conflicts:
                        s = pluralize(conflicts)
                        print('... with {num} conflict{s}.'.format(num=conflicts, s=s))
                except Exception as err:
                    # Use broad exception, we don't want to stop the batch
                    print('!!! Error, skipping {}'.format(filename))
                    errors.append({'filename': filename, 'message': err.message})

        print('\nThe following files were skipped due to errors')
        for err in errors:
            print(u'    {file} : {msg}'.format(file=err['filename'], msg=err['message']))
