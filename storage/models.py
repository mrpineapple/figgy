# encoding: utf-8

from django.db import models


class BaseModel(models.Model):
    """Base class for all models"""
    created_time = models.DateTimeField(
        'date created', auto_now_add=True)
    last_modified_time = models.DateTimeField(
        'last-modified', auto_now=True, db_index=True)

    def save(self, *args, **kwargs):

        # SQLite does not honor CharField max_length; calling full_clean is one work-around to force
        # the validation. However, this will raise a ValidationError, where as I believe most other
        # backends will properly raise a DatabaseError.
        # This is a temporary fix until we figure out what's next. While it works okay for
        # processing XML files, it may not be appropriate in other cases.
        self.full_clean()
        super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Book(BaseModel):
    """Main storage for a Book object"""
    title = models.CharField(
        max_length=128, db_index=True, null=False, blank=False,
        help_text='The title of this book.')
    description = models.TextField(
        blank=True, null=True, default=None,
        help_text='Very short description of this book.')

    def __unicode__(self):
        return u'Book "{0}"'.format(self.title)

    class Meta:
        ordering = ['title']


class Alias(BaseModel):
    """Alternate identifiers for a given book.

    For example, a book can be referred to with an ISBN-10 (older, deprecated scheme), ISBN-13
    (newer scheme), or any number of other aliases. In addition to the publisher-provided aliases
    we create an alias 'PUB_ID' for the book id they provide.
    """

    book = models.ForeignKey(
        Book, related_name='aliases')
    value = models.CharField(
        max_length=255, db_index=True,
        help_text='The value of this identifier')
    scheme = models.CharField(
        max_length=40,
        help_text='The scheme of identifier')

    class Meta:
        unique_together = ('book', 'scheme', 'value')

    def __unicode__(self):
        return u'"{0}": {1}/{2}'.format(self.book.title, self.scheme, self.value)


class Conflict(BaseModel):
    """Record of a Book for which another Book has the same alias.

    When importing a Book from a publisher, we sometimes get incorrect data, if that
    happens we generate a Conflict. We (will) have a tool that manages Conflicts
    and allows someone to manage conflicts (merge or correct and mark distinct).
    """
    book = models.ForeignKey(
        Book, related_name='conflicted_books')
    alias = models.ForeignKey(
        Alias, related_name='conflicted_aliases')
    description = models.CharField(
        max_length=40, null=True, blank=True)

    class Meta:
        unique_together = ('book', 'alias')

    def __unicode__(self):
        return u'"{0}": {1} / {2}'.format(
            self.book.title, self.alias.scheme, self.alias.value)
