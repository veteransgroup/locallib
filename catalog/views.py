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
    # 继承 LoginRequiredMixin 则表示本视图必须登录才能访问 
    # ListView 默认模板为 <模型名>_list.html；可用 template_name 属性指定别的模板
    # html模板中可使用 object_list 或 <模型名>_list 模板变量引用查询结果
    # ListView 里最少只需要提供 model 属性指明模型类即可    
    model = Book
    # 加 paginate_by 属性就支持分页了（模板中要相应支持）
    paginate_by = 10
    # 覆写 get_queryset 可自定义查询结果
    def get_queryset(self):
        return Book.objects.filter(deleted_at=None)

class BookDetailView(generic.DetailView):
    # DetailView 默认的模板为 <模型名>_detail.html
    # html模板中可使用 object 或 <模型名> 模板变量引用查询结果
    # DetailView 里最少只需要提供 model 属性指明模型类即可  
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10
    def get_queryset(self):
        return Author.objects.filter(deleted_at=None)

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
    # CreateView 默认的模板为: <模型名>_form.html；可用 template_name 属性指定别的模板
    # html模板中表单要写<form method="post" enctype="multipart/form-data">才支持文件上传 
    # html模板中可用 form 模板变量代表模型表单 
    # CreateView 里最少只需要提供 model 和 fields 两个属性即可，且无需自己建 Form 类 
    model = Author    
    fields = ('first_name','last_name','date_of_birth','date_of_death')     
    # exclude = ['deleted_at'] # CreateView 不支持 exclude 属性

    # initial 属性可以在新建记录时设置字段的默认值
    initial={'date_of_death':'05/01/2089',}
    # 成功后默认跳转地址为模型类里定义的 get_absolute_url 方法
    # 覆写 get_success_url 可修改成功后跳转的地址；我在此做了额外的业务逻辑（视情况update关联记录）
    def get_success_url(self):
        book_pk = self.request.GET.get('book')
        if book_pk is not None:
            book = get_object_or_404(Book, pk = book_pk)
            book.author = self.object     # self.object 为当前对象
            book.save()
            return reverse('book-detail', kwargs={'pk': book_pk})
        return reverse('author-detail', kwargs={'pk': self.object.pk})

class AuthorUpdate(UpdateView):
    # UpdateView 默认的模板为: <模型名>_form.html；可用 template_name 属性指定别的模板
    # CreateView 和 UpdateView 默认情况下是共用模板的
    # UpdateView 里最少只需要提供 model 和 fields 两个属性即可
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']
    # 成功后默认跳转地址为模型类里定义的 get_absolute_url 方法

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    # 继承 PermissionRequiredMixin 表示本视图必须拥有下面 permission_required 申明的权限才能操作
    # DeleteView 默认模板为: <模型名>_confirm_delete.html
    # CreateView 里最少只需要提供 model 和 success_url 两个属性即可
    model = Author
    success_url = reverse_lazy('authors')
    # permission_required 申明的权限是在 model 里定义的，但是不要求一定定义在 Author （本次用的）模型下
    permission_required = 'catalog.can_mark_returned'


class BookCreate(CreateView):
    model = Book
    fields = ('title','author','summary','isbn','genre','cover','language')
    # fields = '__all__'    
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
    fields = ('title','author','summary','isbn','genre','cover','language')
    template_name ='catalog/author_form.html'
    

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'
    template_name ='catalog/author_confirm_delete.html'

    # 因为想共用模板，所以覆写 get_context_data 传变量到模板，以便模板里区分到底是哪个view在用
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