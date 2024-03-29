from django.http import response
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .forms import RenewBookForm
from django.contrib.auth.decorators import permission_required
import datetime
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from catalog.models import Author, Book, BookInstance, LibUser
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from pure_pagination.mixins import PaginationMixin


@csrf_exempt
def hello(request):
    result = {
        'code': 0,
        'message': 'success',
        'data': [],
    }
    return JsonResponse(result)


def intro(request):
    if request.method == 'POST':
        raise response.Http404
    return render(request, 'introduction.html')


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
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1

    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances, 'num_visits': num_visits,
                 'num_instances_available': num_instances_available, 'num_authors': num_authors},
    )


class BookListView(PaginationMixin, generic.ListView):
    # 继承 LoginRequiredMixin 则表示本视图必须登录才能访问
    # ListView 默认模板为 <模型名>_list.html；可用 template_name 属性指定别的模板
    # html模板中可使用 object_list 或 <模型名>_list 模板变量引用查询结果
    # ListView 里最少只需要提供 model 属性指明模型类即可
    model = Book
    # 加 paginate_by 属性就支持分页了（模板中要相应支持）
    paginate_by = settings.PAGE_SIZE
    # 覆写 get_queryset 可自定义查询结果

    def get_queryset(self):
        search = self.request.GET.get('q')
        queryset = Book.objects.all()
        if search:
            queryset = queryset.filter(title__icontains=search)
        if self.request.GET.get('del') is not None:
            return queryset.filter(deleted_at__isnull=False)
        return queryset.filter(deleted_at=None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('del'):
            context['admin'] = 'Yes'
        if self.request.GET.get('q'):
            context['q'] = self.request.GET.get('q')
        return context


class BookDetailView(generic.DetailView):
    # DetailView 默认的模板为 <模型名>_detail.html
    # html模板中可使用 object 或 <模型名> 模板变量引用查询结果
    # DetailView 里最少只需要提供 model 属性指明模型类即可
    model = Book

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.visit()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookinstance_set'] = BookInstance.objects.filter(
            deleted_at=None).filter(book=self.object).order_by('-status')
        return context


class AuthorListView(PaginationMixin, generic.ListView):
    model = Author
    paginate_by = settings.PAGE_SIZE

    def get_queryset(self):
        search = self.request.GET.get('q')
        queryset = Author.objects.all()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search))
        if self.request.GET.get('del') is not None:
            return queryset.filter(deleted_at__isnull=False)
        return queryset.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('del') is not None:
            context['admin'] = 'Yes'
        if self.request.GET.get('q'):
            context['q'] = self.request.GET.get('q')
        return context


class AuthorDetailView(generic.DetailView):
    model = Author

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book_set'] = Book.objects.filter(
            deleted_at=None).filter(author=self.object)
        return context


class LoanedBooksByUserListView(LoginRequiredMixin, PaginationMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user. 
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed.html'
    paginate_by = settings.PAGE_SIZE

    def get_queryset(self):
        search = self.request.GET.get('q')
        if search:
            books = Book.objects.filter(title__icontains=search)
            return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').filter(Q(book__in=books) | Q(imprint__icontains=search)).order_by('due_back')
        else:
            return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('q'):
            context['q'] = self.request.GET.get('q')
        return context


class LoanedBooksListView(PermissionRequiredMixin, PaginationMixin, generic.ListView):
    model = BookInstance
    paginate_by = settings.PAGE_SIZE
    permission_required = 'catalog.can_mark_returned'
    # can share template like this:
    template_name = 'catalog/bookinstance_list_borrowed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all'] = True
        if self.request.GET.get('q'):
            context['q'] = self.request.GET.get('q')
        return context

    def get_queryset(self):
        search = self.request.GET.get('q')
        if search:
            books = Book.objects.filter(title__icontains=search)
            return BookInstance.objects.filter(status__exact='o').filter(Q(book__in=books) | Q(imprint__icontains=search)).order_by('due_back')
        else:
            return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_renew')
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()
            messages.add_message(
                request, messages.INFO, "The book has renewed to %s" % form.cleaned_data['renewal_date'])
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date, })

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})


@login_required
def lend_book(request, pk):
    book_inst = get_object_or_404(BookInstance, pk=pk)
    user = get_object_or_404(LibUser, username=request.user)
    if user.email is None or user.email == '':
        messages.add_message(
            request, messages.INFO, 'You can lend book instance after you register your email.')
        return HttpResponseRedirect(reverse('user-detail', kwargs={'pk': user.id}))
    if request.method == 'POST':
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.borrower = request.user
            book_inst.status = 'o'
            book_inst.save()
            messages.add_message(
                request, messages.INFO, "You have lended book: %s" % book_inst.book.title)
            return HttpResponseRedirect(reverse('my-borrowed'))
    else:
        proposed_return_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_return_date, })
    return render(request, 'catalog/lend_bookinstance_form.html', {'form': form, 'bookinst': book_inst})


class AuthorCreate(LoginRequiredMixin, CreateView):
    # CreateView 默认的模板为: <模型名>_form.html；可用 template_name 属性指定别的模板
    # html模板中表单要写<form method="post" enctype="multipart/form-data">才支持文件上传
    # html模板中可用 form 模板变量代表模型表单
    # CreateView 里最少只需要提供 model 和 fields 两个属性即可，且无需自己建 Form 类
    model = Author
    fields = ('first_name', 'last_name', 'date_of_birth', 'date_of_death')
    # exclude = ['deleted_at'] # CreateView 不支持 exclude 属性; Django REST Framework 在序列化器里面支持 exclude

    # initial 属性可以在新建记录时设置字段的默认值
    # initial = {'date_of_death': '05/01/2089', }
    # 成功后默认跳转地址为模型类里定义的 get_absolute_url 方法
    # 覆写 get_success_url 可修改成功后跳转的地址；我在此做了额外的业务逻辑（视情况update关联记录:如果是从 book 记录入口创建 author，那么book的 author 值改为新增的 author）

    def get_success_url(self):
        book_pk = self.request.GET.get('book')
        messages.add_message(self.request, messages.SUCCESS,
                             "Added author: %s" % self.object)
        if book_pk is not None:
            book = get_object_or_404(Book, pk=book_pk)
            book.author = self.object     # self.object 为当前对象
            book.save()
            return reverse('book-detail', kwargs={'pk': book_pk})
        return reverse('author-detail', kwargs={'pk': self.object.pk})


class AuthorUpdate(LoginRequiredMixin, UpdateView):
    # UpdateView 默认的模板为: <模型名>_form.html；可用 template_name 属性指定别的模板
    # CreateView 和 UpdateView 默认情况下是共用模板的
    # UpdateView 里最少只需要提供 model 和 fields 两个属性即可
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    # 成功后默认跳转地址为模型类里定义的 get_absolute_url 方法


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    # 继承 PermissionRequiredMixin 表示本视图必须拥有下面 permission_required 申明的权限才能操作
    # DeleteView 默认模板为: <模型名>_confirm_delete.html
    # CreateView 里最少只需要提供 model 和 success_url 两个属性即可
    model = Author
    success_url = reverse_lazy('authors')
    # permission_required 申明的权限是在 model 里定义的，但是不要求一定定义在 Author （本次用的）模型下
    permission_required = 'catalog.can_mark_returned'


class BookCreate(LoginRequiredMixin, CreateView):
    model = Book
    fields = ('title', 'author', 'summary',
              'isbn', 'genre', 'cover', 'language')
    # fields = '__all__'
    initial = {'isbn': '00090476218', }
    template_name = 'catalog/author_form.html'

    # 覆写 get_initial 修改默认值，如果是从 author 记录入口创建book，那么默认填上 author
    def get_initial(self):
        initial_data = super().get_initial()
        initial_data['author'] = self.request.GET.get('author')
        return initial_data

    # 覆写 get_success_url 修改成功后跳转的地址，从哪里来回哪里去
    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS,
                             "Added book: %s" % self.object)
        if self.request.GET.get('author'):
            return reverse('author-detail', kwargs={'pk': self.request.GET.get('author')})
        return reverse('book-detail', kwargs={'pk': self.object.pk})


class BookUpdate(LoginRequiredMixin, UpdateView):
    model = Book
    fields = ('title', 'author', 'summary',
              'isbn', 'genre', 'cover', 'language')
    template_name = 'catalog/author_form.html'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/author_confirm_delete.html'

    # 因为想共用模板，所以覆写 get_context_data 传变量到模板，以便模板里区分到底是哪个view在用
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['flag'] = True
        return context


@permission_required('catalog.can_renew')
def common_delete(request, pk):
    target = request.GET.get('del', '')
    if target == 'author':
        obj = get_object_or_404(Author, pk=pk)
        redirect_to = reverse('authors')
        redirect_to_del = reverse('author_delete', kwargs={'pk': pk, })
    elif target == 'book':
        obj = get_object_or_404(Book, pk=pk)
        # redirect_to = '/catalog/books/'
        # 上面是硬编码，所以注释了, 改用 reverse 函数通过名字反向解析出url路径
        redirect_to = reverse('books')
        redirect_to_del = reverse('book_delete', args=[pk])
    elif target == 'bookinstance':
        obj = get_object_or_404(BookInstance, pk=pk)
        book_id = request.GET.get('book')
        if obj.status == 'o':
            book = get_object_or_404(Book, pk=book_id)
            messages.add_message(
                request, messages.WARNING, "Can't delete this book instance due to its on loan status")
            return render(request, 'catalog/book_detail.html', {'book': book, 'object': book,
                                                                'warn': "Can't delete this book instance due to its on loan status",
                                                                'bookinstance_set': BookInstance.objects.filter(deleted_at=None).filter(book=book).order_by('-status')})
        redirect_to = reverse('book-detail', args=[book_id])
        redirect_to_del = reverse('bookinstance_delete', args=[pk])
    else:
        return reverse('index')
    if obj.deleted_at is None:
        obj.deleted_at = timezone.now()
        obj.save()
        messages.add_message(request, messages.SUCCESS,
                             "Success deleted: %s" % obj)
        return redirect(redirect_to)
    else:
        return redirect(redirect_to_del)


@permission_required('catalog.can_renew')
def common_restore(request, pk):
    target = request.GET.get('obj', '')
    if target == 'author':
        obj = get_object_or_404(Author, pk=pk)
        redirect_to = reverse('author-detail', args=[pk])
    elif target == 'book':
        obj = get_object_or_404(Book, pk=pk)
        # redirect_to = '/catalog/books/'
        # 上面是硬编码，所以注释了, 改用 reverse 函数通过名字反向解析出url路径
        redirect_to = reverse('book-detail', args=[pk])
    elif target == 'bookinstance':
        obj = get_object_or_404(BookInstance, pk=pk)
        redirect_to = reverse('bookinstances')
    else:
        return reverse('index')

    obj.deleted_at = None
    obj.save()
    messages.add_message(request, messages.SUCCESS,
                         "Success restored: %s" % obj)
    return redirect(redirect_to)


class BookInstanceListView(PermissionRequiredMixin, PaginationMixin, generic.ListView):
    model = BookInstance
    paginate_by = settings.PAGE_SIZE
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        search = self.request.GET.get('q')
        if search:
            books = Book.objects.filter(title__icontains=search)
            if self.request.GET.get('del') is not None:
                return BookInstance.objects.filter(deleted_at__isnull=False).filter(Q(book__in=books) | Q(imprint__icontains=search))
            return BookInstance.objects.all().filter(Q(book__in=books) | Q(imprint__icontains=search))
        else:
            if self.request.GET.get('del') is not None:
                return BookInstance.objects.filter(deleted_at__isnull=False)
            return BookInstance.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('q'):
            context['q'] = self.request.GET.get('q')
        return context


class BookInstanceCreate(PermissionRequiredMixin, CreateView):
    model = BookInstance
    fields = ('book', 'imprint', 'status')
    initial = {'status': 'a', }
    template_name = 'catalog/author_form.html'
    permission_required = 'catalog.can_mark_returned'

    def get_initial(self):
        initial_data = super().get_initial()
        initial_data['book'] = self.request.GET.get('book')
        return initial_data

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS,
                             "Added book instance: %s" % self.object)
        if self.request.GET.get('book'):
            return reverse('book-detail', kwargs={'pk': self.request.GET.get('book')})
        return reverse('bookinstances')


class BookInstanceUpdate(PermissionRequiredMixin, UpdateView):
    model = BookInstance
    fields = ('book', 'imprint', 'status', 'borrower', 'status')
    template_name = 'catalog/author_form.html'
    permission_required = 'catalog.can_mark_returned'


class BookInstanceDelete(PermissionRequiredMixin, DeleteView):
    model = BookInstance
    success_url = reverse_lazy('bookinstances')
    permission_required = 'catalog.can_mark_returned'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == 'o' and self.object.borrower is not None:
            # return HttpResponseRedirect(reverse('bookinstances'))
            messages.add_message(
                request, messages.ERROR, "Can't delete this book instance due to its on loan by %s" % self.object.borrower)
            return render(request, 'catalog/bookinstance_list.html', {'object_list': BookInstance.objects.all(),
                                                                      'warn': "Can't delete this book instance due to its on loan by %s" % self.object.borrower})
        else:
            return super().delete(request, *args, **kwargs)


class UserDetailView(LoginRequiredMixin, generic.DetailView):
    model = LibUser


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = LibUser
    fields = ['first_name', 'last_name', 'card_No', 'phone', 'photo']
