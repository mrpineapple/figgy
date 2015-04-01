# encoding: utf-8

# Created by David Rideout <drideout@safaribooksonline.com> on 2/7/14 4:56 PM
# Copyright (c) 2013 Safari Books Online, LLC. All rights reserved.

from lxml import etree

from django.core.management.base import BaseCommand

import storage.tools


class Command(BaseCommand):
    args = '<filename filename2 filename3 ...>'
    help = 'Process an xml file '

    def handle(self, *args, **options):
        print ''
        print 'Processing {0} titles\n'.format(len(args))
        for filename in args:
            with open(filename, 'rb') as fh:
                print 'Importing %s into database.' % filename
                book_node = etree.parse(fh).getroot()
                title, conflicts = storage.tools.process_book_element(book_node)
                print '... "{0}" processed'.format(title)
                if conflicts:
                    print '!!! with {0} conflicts'.format(conflicts)
        print ''
