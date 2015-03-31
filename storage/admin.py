from django.contrib import admin

from storage.models import Book, Alias


class InlineAliasAdmin(admin.StackedInline):
    model = Alias
    extra = 0


class BookAdmin(admin.ModelAdmin):
    inlines = [InlineAliasAdmin]

    list_display = ['id', 'title', 'list_aliases']

    def list_aliases(self, obj):
        if obj:
            return '<pre>%s</pre>' % '\n'.join([o.value for o in obj.aliases.all()])

    list_aliases.allow_tags = True

admin.site.register(Book, BookAdmin)
