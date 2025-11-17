"""
Category views.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from ..models import Category, Article


class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories."""
    model = Category
    template_name = 'knowledge/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
            is_deleted=False,
            parent__isnull=True
        ).prefetch_related('children').order_by('order', 'name')


def category_detail(request, slug):
    """View articles in a category."""
    category = get_object_or_404(
        Category.objects.prefetch_related('children'),
        slug=slug,
        is_active=True,
        is_deleted=False
    )

    # Get articles in this category and subcategories
    category_ids = [category.pk]
    for child in category.get_descendants():
        category_ids.append(child.pk)

    articles = Article.objects.filter(
        category_id__in=category_ids,
        status=Article.Status.PUBLISHED,
        is_deleted=False
    ).order_by('-is_pinned', '-is_featured', '-published_at')

    context = {
        'category': category,
        'articles': articles,
        'subcategories': category.children.filter(is_active=True, is_deleted=False),
        'breadcrumbs': category.get_ancestors() + [category],
    }

    return render(request, 'knowledge/category_detail.html', context)
