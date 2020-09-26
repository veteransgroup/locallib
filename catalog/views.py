from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from catalog.models import Author, Book, BookInstance
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import logging

# Create your views here.
@csrf_exempt
def hello(request):
    result = {
        'code': 0,
        'message': 'success',
        'data': [],
    }
    return JsonResponse(result)


def index(request):
    """
    View function for home page of site.
    """
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(
        status__exact='a').count()
    num_authors = Author.objects.count()  # The 'all()' is implied by default.
    # Number of visits to this view, as counted in the session variable.
    num_visits=request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1

    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances, 'num_visits':num_visits,
                 'num_instances_available': num_instances_available, 'num_authors': num_authors},
    )

class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(LoginRequiredMixin,generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """
    Generic class-based view listing books on loan to current user. 
    """
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoanedBooksListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'
    # can share template like this:
    template_name ='catalog/bookinstance_list_borrowed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all'] = True
        return context

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib.auth.decorators import permission_required
from .forms import RenewBookForm

@permission_required('catalog.can_renew')
def renew_book_librarian(request, pk):
    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from catalog.forms import RegisterForm

class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'    
    initial={'date_of_death':'05/01/2089',}
    
    def get_success_url(self):
        book_pk = self.request.GET.get('book')
        if book_pk is not None:
            book = get_object_or_404(Book, pk = book_pk)
            book.author = self.object
            book.save()
            return reverse('book-detail', kwargs={'pk': book_pk})
        return reverse('author-detail', kwargs={'pk': self.object.pk})

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.can_mark_returned'


class BookCreate(CreateView):
    model = Book
    fields = '__all__'    
    initial={'isbn':'00090476218',}
    template_name ='catalog/author_form.html'

    def get_initial(self):
        initial_data = super().get_initial()
        initial_data['author'] = self.request.GET.get('author')
        return initial_data
    
    def get_success_url(self):
        if self.request.GET.get('author'):
            return reverse('author-detail', kwargs={'pk': self.request.GET.get('author')})
        return reverse('book-detail', kwargs={'pk': self.object.pk})


class BookUpdate(UpdateView):
    model = Book
    fields = '__all__'
    template_name ='catalog/author_form.html'
    

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'
    template_name ='catalog/author_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flag'] = True
        return context

def register(request):
    redirect_to = request.POST.get('next', request.GET.get('next', ''))

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            if redirect_to:
                return redirect(redirect_to)
            else:
                return reverse('login')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', context={'form': form, 'next': redirect_to})