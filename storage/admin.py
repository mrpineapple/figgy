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

    list_display = ['title', 'id', 'list_aliases']

    def list_aliases(self, obj):
        if obj:
            return '<pre>%s</pre>' % '\n'.join(
                ['%s: %s' % (o.scheme, o.value) for o in obj.aliases.all().order_by('scheme')]
            )

    list_aliases.allow_tags = True

admin.site.register(Book, BookAdmin)
