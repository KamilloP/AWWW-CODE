from django.contrib import admin
# from .models import Author, Genre, Book, BookInstance
from .models import Folder, File, CodeSection, SectionKind, Status, StatusData 


admin.site.register(Folder)
admin.site.register(File)
admin.site.register(CodeSection)
admin.site.register(SectionKind)
admin.site.register(Status)
admin.site.register(StatusData)

# # admin.site.register(Author)
# class AuthorAdmin(admin.ModelAdmin):
#     list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')
#     fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
# admin.site.register(Author, AuthorAdmin)

# admin.site.register(Genre)

# admin.site.register(BookInstance)
# admin.site.register(Book)

# Register the Admin classes for BookInstance using the decorator
# @admin.register(BookInstance)
# class BookInstanceAdmin(admin.ModelAdmin):
#     list_display = ('book', 'status', 'borrower', 'due_back', 'id')
#     list_filter = ('status', 'due_back')
#     fieldsets = (
#         (None, {
#             'fields': ('book', 'imprint', 'id')
#         }),
#         ('Availability', {
#             'fields': ('status', 'due_back', 'borrower')
#         }),
#     )

# class BooksInstanceInline(admin.TabularInline):
#     model = BookInstance

# @admin.register(Book)
# class BookAdmin(admin.ModelAdmin):
#     list_display = ('title', 'author', 'display_genre')
#     inlines = [BooksInstanceInline]