import markdown
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect,get_object_or_404
from django.shortcuts import render
from .forms import ArticlePostForm
from .models import Article
from user.models import BlogUser,Follow
from django.db.models import Q
from comment.models import Comment
from django.contrib.auth.models import User
from comment.forms import CommentForm

# 分类选项
category = {
    "生活": "生活",
    "闲谈": "闲谈",
    "软件": "软件",
    "硬件": "硬件",
    "知识": "知识",
    "美食": "美食",
    "其他": "其他",
}

def list_view(request):
    search_query = request.GET.get('search', '') # 获取搜索词
    selected_category = request.GET.get('category', '') # 获取分类

    articles = Article.objects.all()

    # 由搜索词筛选
    if search_query:
        articles = articles.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))

    # 由分类筛选
    if selected_category:
        articles = articles.filter(category=selected_category)

    # 分页
    articles = Paginator(articles, 10)
    page = request.GET.get('page')
    articles = articles.get_page(page)

    return render(request, 'ArticleList.html', {
        'articles': articles,
        'category': category,
    })

def detail_view(request, id):
    article = Article.objects.get(id=id)
    comments = Comment.objects.filter(article=id)
    comment_form = CommentForm()
    article.looks += 1
    article.save()

    # 判断是否关注了作者
    is_following_author = False
    if request.user.is_authenticated and request.user != article.author:
        is_following_author = Follow.objects.filter(
            follower=request.user,
            followed=article.author
        ).exists()

    article.body = markdown.markdown(article.body, extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite'
        ])
    context = {'article': article,
               'comments': comments,
               'comment_form': comment_form,
               'is_following_author': is_following_author
               }
    return render(request, 'Article.html', context)

@login_required(login_url='/user/login/')
def create_view(request):
    if request.method == 'POST':
        article_post_form = ArticlePostForm(request.POST, request.FILES)
        if article_post_form.is_valid():
            new_article = article_post_form.save(commit=False)
            new_article.author = BlogUser.objects.get(username=request.user.username)
            new_article.save()
            id = new_article.id
            return redirect(f'/article/detail/{id}')
        else:
            return render(request, 'ArticlePost.html', {'article_post_form': article_post_form})
    else:
        article_post_form = ArticlePostForm()
        return render(request, 'ArticlePost.html', {'article_post_form': article_post_form})

@login_required(login_url='/user/login/')
def delete_view(request, id):
    article = Article.objects.get(id=id)
    if request.user.username != article.author.username:
        return redirect('/')
    article.delete()
    return redirect('/article/list')

@login_required(login_url='/user/login/')
def edit_view(request, id):
    article = Article.objects.get(id=id)
    if request.user.username != article.author.username:
        return redirect('/')
    if request.method == 'POST':
        article_post_form = ArticlePostForm(request.POST, request.FILES, instance=article)
        if article_post_form.is_valid():
            article_post_form.save()
            return redirect('/article/list')
        else:
            return render(request, 'ArticlePost.html', {'article_post_form': article_post_form})
    else:
        article_post_form = ArticlePostForm(instance=article)
        return render(request, 'ArticlePost.html', {'article_post_form': article_post_form})

@login_required(login_url='/user/login/')
def my_view(request):
    search_query = request.GET.get('search', '') # 获取搜索词
    selected_category = request.GET.get('category', '') # 获取分类

    articles = Article.objects.filter(author=request.user.id)

    # 由搜索词筛选
    if search_query:
        articles = articles.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))

    # 由分类筛选
    if selected_category:
        articles = articles.filter(category=selected_category)

    # 分页
    articles = Paginator(articles, 10)
    page = request.GET.get('page')
    articles = articles.get_page(page)

    return render(request, 'MyArticle.html', {
        'articles': articles,
        'category': category,
    })
