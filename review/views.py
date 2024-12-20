import datetime
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views import View
from django.http import Http404
from django.core.exceptions import FieldError
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Post, Comment, Category
from .forms import CommentForm, PostForm


class PostList(ListView):
    model = Post
    template_name = 'review/post_list.html'
    paginate_by = 4

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostList, self).get_context_data(**kwargs)
        context['post_count'] = Post.objects.all().count()
        context['category_list'] = Category.objects.all()
        context['posts_without_category'] = Post.objects.filter(category=None).count()

        user_name = None
        if self.request.user.is_authenticated:
            user_name = self.request.user.username  

        context['user_name'] = user_name
        context['search_error'] = self.request.session.get('search_error', None)

        return context
    

class PostDetail(DetailView):
    model = Post
    template_name = 'review/post_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_count'] = Post.objects.all().count()
        context['comment_form'] = CommentForm()

        user_name = None
        if self.request.user.is_authenticated:
            user_name = self.request.user.username  

        context['user_name'] = user_name

        return context
    

class PostCreate(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'review/post_form.html'
    form_class = PostForm
    success_url = reverse_lazy('post_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_name'] = self.request.user.username
        return context

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user.username  
        post.name = self.request.user.username
        if not post.date:
            post.date = datetime.date.today()
        post.save()
        return redirect('review:review_detail', pk=post.pk)

    def get_login_url(self):
        login_url = super().get_login_url() or reverse_lazy('account_login')
        return f'{login_url}?next={self.request.path}'
    

class PostUpdate(UpdateView):
    model = Post
    template_name = 'review/post_form.html'
    fields = ['content', 'title', 'date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_name'] = self.request.user.username
        return context


class CommentCreate(View):
    def get(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        user_name = None
        if request.user.is_authenticated:
            user_name = request.user.username  

        comment_form = CommentForm()
        
        context = {
            'post': post,
            'user_name': user_name,
            'comment_form': comment_form,
        }

        return render(request, 'review/post_detail.html', context)

    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)

        user_name = None
        if request.user.is_authenticated:
            user_name = request.user.username  

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = user_name
            comment.save()
            return redirect(post.get_absolute_url())  

        context = {
            'post': post,
            'user_name': user_name,
            'comment_form': comment_form,
        }
        return render(request, 'review/post_detail.html', context)


class CommentUpdate(UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'review/comment_form.html'

    def get_object(self, queryset=None):
        comment = super().get_object(queryset)        
        user_name = None

        if self.request.user.is_authenticated:
            user_name = self.request.user.username  

        if comment.author != user_name:
            raise PermissionDenied('No right to edit')

        return comment
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_name = None
        if self.request.user.is_authenticated:
            user_name = self.request.user.username  

        context['user_name'] = user_name
        return context

    def get_success_url(self):
        post = self.get_object().post
        return post.get_absolute_url() + '#comment-list'


class CommentDelete(DeleteView):
    model = Comment
    template_name = 'review/comment_confirm_delete.html'

    def get_object(self, queryset=None):
        comment = super().get_object(queryset)        
        user_name = None

        if self.request.user.is_authenticated:
            user_name = self.request.user.username  

        if comment.author != user_name:
            raise PermissionDenied('No right to delete Comment')

        return comment
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_name = None
        if self.request.user.is_authenticated:
            user_name = self.request.user.username  

        context['user_name'] = user_name
        return context

    def get_success_url(self):
        post = self.get_object().post
        return post.get_absolute_url() + '#comment-list'
    

class PostSearch(PostList):
    def get_queryset(self):
        q = self.kwargs['q']
        try:
            object_list = Post.objects.filter(
                Q(title__icontains=q) | 
                Q(content__icontains=q) | 
                Q(name__icontains=q)  
            )
        except FieldError:
            raise Http404(f"No results found for '{q}'")
        return object_list

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_info'] = f'Search: "{self.kwargs["q"]}"'
        return context
    

class PostCategory(ListView):

    def get_queryset(self):
        slug = self.kwargs['slug']

        if slug == '_none':
            category = None
        else:
            category = Category.objects.get(slug=slug)

        return Post.objects.filter(category=category).order_by('-created')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(type(self), self).get_context_data(**kwargs)
        context['category_list'] = Category.objects.all()
        context['posts_without_category'] = Post.objects.filter(category=None).count()

        slug = self.kwargs['slug']

        if slug == '_none':
            context['category'] = '미분류'
        else:
            category = Category.objects.get(slug=slug)
            context['category'] = category

        return context
