"""
Article views for Knowledge Center.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone

from ..models import Article, ArticleAcknowledgment, Category, Tag
from ..services import KnowledgeService
from ..forms import ArticleForm


class ArticleListView(LoginRequiredMixin, ListView):
    """List all published articles with filtering and search."""
    model = Article
    template_name = 'knowledge/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        qs = Article.objects.filter(
            status=Article.Status.PUBLISHED,
            is_deleted=False
        ).select_related('category', 'owner_department').prefetch_related('tags')

        # Search
        query = self.request.GET.get('q', '')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(summary__icontains=query) |
                Q(body__icontains=query) |
                Q(code__icontains=query)
            )

        # Filter by type
        article_type = self.request.GET.get('type', '')
        if article_type:
            qs = qs.filter(article_type=article_type)

        # Filter by category
        category = self.request.GET.get('category', '')
        if category:
            qs = qs.filter(category__slug=category)

        # Filter by tag
        tag = self.request.GET.get('tag', '')
        if tag:
            qs = qs.filter(tags__slug=tag)

        # Filter by department
        department = self.request.GET.get('department', '')
        if department:
            qs = qs.filter(owner_department_id=department)

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            is_active=True, is_deleted=False
        )
        context['tags'] = Tag.objects.all()
        context['article_types'] = Article.ArticleType.choices
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'type': self.request.GET.get('type', ''),
            'category': self.request.GET.get('category', ''),
            'tag': self.request.GET.get('tag', ''),
            'department': self.request.GET.get('department', ''),
        }
        return context


class ArticleDetailView(LoginRequiredMixin, DetailView):
    """View single article with full content."""
    model = Article
    template_name = 'knowledge/article_detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Article.objects.filter(is_deleted=False).select_related(
            'category', 'owner_department', 'created_by', 'approved_by'
        ).prefetch_related('tags', 'attachments', 'article_attachments')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.increment_view()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        # Check if user has acknowledged
        context['user_acknowledged'] = ArticleAcknowledgment.objects.filter(
            article=article,
            user=self.request.user
        ).exists()

        # Related articles
        context['related_articles'] = article.related_articles.filter(
            status=Article.Status.PUBLISHED,
            is_deleted=False
        )[:5]

        # Articles in same category
        if article.category:
            context['category_articles'] = Article.objects.filter(
                category=article.category,
                status=Article.Status.PUBLISHED,
                is_deleted=False
            ).exclude(pk=article.pk)[:5]

        # Version history
        context['versions'] = article.all_versions[:10]

        return context


class ArticleCreateView(PermissionRequiredMixin, CreateView):
    """Create new article."""
    model = Article
    form_class = ArticleForm
    template_name = 'knowledge/article_form.html'
    permission_required = 'knowledge.add_article'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = Article.Status.DRAFT
        messages.success(self.request, 'Article created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('knowledge:article_detail', kwargs={'slug': self.object.slug})


class ArticleUpdateView(PermissionRequiredMixin, UpdateView):
    """Edit existing article."""
    model = Article
    form_class = ArticleForm
    template_name = 'knowledge/article_form.html'
    permission_required = 'knowledge.change_article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Article.objects.filter(is_deleted=False)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Article updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('knowledge:article_detail', kwargs={'slug': self.object.slug})


@login_required
def article_acknowledge(request, pk):
    """User acknowledges reading an article."""
    article = get_object_or_404(Article, pk=pk, is_deleted=False)

    if not article.requires_acknowledgment:
        messages.warning(request, 'This article does not require acknowledgment.')
        return redirect('knowledge:article_detail', slug=article.slug)

    acknowledgment, created = ArticleAcknowledgment.objects.get_or_create(
        article=article,
        user=request.user,
        defaults={
            'ip_address': request.META.get('REMOTE_ADDR')
        }
    )

    if created:
        messages.success(request, 'Thank you for acknowledging this article.')
    else:
        messages.info(request, 'You have already acknowledged this article.')

    return redirect('knowledge:article_detail', slug=article.slug)


@login_required
@permission_required('knowledge.can_publish_article')
def article_publish(request, pk):
    """Publish an approved article."""
    article = get_object_or_404(Article, pk=pk, is_deleted=False)

    try:
        KnowledgeService.publish_article(article, request.user)
        messages.success(request, f'Article "{article.title}" has been published.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('knowledge:article_detail', slug=article.slug)


@login_required
def article_search_api(request):
    """API for article search (used by autocomplete)."""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    articles = Article.objects.filter(
        status=Article.Status.PUBLISHED,
        is_deleted=False
    ).filter(
        Q(title__icontains=query) |
        Q(code__icontains=query) |
        Q(summary__icontains=query)
    )[:10]

    results = [
        {
            'id': article.pk,
            'code': article.code,
            'title': article.title,
            'type': article.get_article_type_display(),
            'url': reverse_lazy('knowledge:article_detail', kwargs={'slug': article.slug})
        }
        for article in articles
    ]

    return JsonResponse({'results': results})
