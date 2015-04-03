from django.contrib import admin

from storage.models import Alias, Book, Conflict


class InlineAliasAdmin(admin.StackedInline):
    model = Alias
    extra = 0


class InlineConflictAdmin(admin.StackedInline):
    model = Conflict
    extra = 0


class BookAdmin(admin.ModelAdmin):
    inlines = [InlineConflictAdmin, InlineAliasAdmin]

    list_display = ['title', 'id', 'list_aliases', 'list_conflicts']

    def list_aliases(self, obj):
        if obj:
            return '<pre>{}</pre>'.format('\n'.join(
                ['{0: <9}: {1}'.format(o.scheme, o.value)
                 for o in obj.aliases.all().order_by('scheme')])
            )

    list_aliases.allow_tags = True

    def list_conflicts(self, obj):
        if obj:
            conflicts = Conflict.objects.filter(book=obj)
            return '<pre>{}</pre>'.format('\n'.join(
                ['{title}: {scheme}/{value}'.format(
                    title=conflict.alias.book.title,
                    scheme=conflict.alias.scheme,
                    value=conflict.alias.value)
                 for conflict in conflicts.all().order_by('book__title')])
            )

    list_conflicts.allow_tags = True


admin.site.register(Book, BookAdmin)
