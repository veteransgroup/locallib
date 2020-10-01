from django.urls import path
from catalog import views

urlpatterns = [
    path('hello', views.hello),
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'),
    path('book/create/', views.BookCreate.as_view(), name='book_create'),
    path('book/<int:pk>/update/', views.BookUpdate.as_view(), name='book_update'),
    path('book/<int:pk>/delete/', views.BookDelete.as_view(), name='book_delete'),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('author/<int:pk>', views.AuthorDetailView.as_view(), name='author-detail'),
    path('author/create/', views.AuthorCreate.as_view(), name='author_create'),
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author_update'),
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author_delete'),
    path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),
    path('allborrowed/', views.LoanedBooksListView.as_view(), name='all-borrowed'),
    path('book/<uuid:pk>/renew/', views.renew_book_librarian, name='renew-book-librarian'),
    path('delete/<int:pk>/', views.common_delete, name='common_delete'),
    path('delete/<uuid:pk>/', views.common_delete, name='common_delete2'),
    path('restore/<int:pk>/', views.common_restore, name='restore'),
    path('restore/<uuid:pk>/', views.common_restore, name='restore2'),
    path('bookinstances/', views.BookInstanceListView.as_view(), name='bookinstances'),
    path('bookinstance/create/', views.BookInstanceCreate.as_view(), name='bookinstance_create'),
    path('bookinstance/<uuid:pk>/update/', views.BookInstanceUpdate.as_view(), name='bookinstance_update'),
    path('bookinstance/<uuid:pk>/delete/', views.BookInstanceDelete.as_view(), name='bookinstance_delete'),
]