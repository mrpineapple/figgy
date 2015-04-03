# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 4:56 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

from lxml import etree

from django.core.management.base import BaseCommand

import storage.tools as tools


class Command(BaseCommand):
    args = '<filename filename2 filename3 ...>'
    help = 'Process an xml file '

    def handle(self, *args, **options):
        print
        print 'Processing {0} titles\n'.format(len(args))
        for filename in args:
            with open(filename, 'rb') as fh:
                contents = fh.read()
                sha1 = tools.hash_data(contents)

                print 'Importing {0} into database.'.format(filename)
                try:
                    book_node = etree.fromstring(contents)
                    conflicts = tools.process_book_element(book_node, filename, sha1)
                    if conflicts:
                        s = 's' if conflicts > 1 else ''
                        print '... created with {num} conflict{s}.'.format(num=conflicts, s=s)
                except etree.XMLSyntaxError:
                    print('!!! Bad XML file, skipping.')
        print
