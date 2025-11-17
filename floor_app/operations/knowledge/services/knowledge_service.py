"""
Knowledge Service - Business logic for knowledge articles.
"""
from django.db.models import Q, Count
from django.utils import timezone


class KnowledgeService:
    """Service layer for knowledge article operations."""

    @staticmethod
    def search_articles(query, filters=None):
        """
        Search articles by keyword with optional filters.

        Args:
            query: search term
            filters: dict of filter parameters
        """
        from floor_app.operations.knowledge.models import Article

        qs = Article.objects.filter(
            status=Article.Status.PUBLISHED,
            is_deleted=False
        )

        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(summary__icontains=query) |
                Q(body__icontains=query) |
                Q(code__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()

        if filters:
            if filters.get('article_type'):
                qs = qs.filter(article_type=filters['article_type'])
            if filters.get('category'):
                qs = qs.filter(category_id=filters['category'])
            if filters.get('department'):
                qs = qs.filter(owner_department_id=filters['department'])
            if filters.get('tags'):
                qs = qs.filter(tags__id__in=filters['tags'])
            if filters.get('priority'):
                qs = qs.filter(priority=filters['priority'])

        return qs

    @staticmethod
    def get_featured_articles(limit=5):
        """Get featured articles."""
        from floor_app.operations.knowledge.models import Article

        return Article.objects.filter(
            status=Article.Status.PUBLISHED,
            is_featured=True,
            is_deleted=False
        ).order_by('-published_at')[:limit]

    @staticmethod
    def get_recent_articles(limit=10):
        """Get recently published articles."""
        from floor_app.operations.knowledge.models import Article

        return Article.objects.filter(
            status=Article.Status.PUBLISHED,
            is_deleted=False
        ).order_by('-published_at')[:limit]

    @staticmethod
    def get_popular_articles(limit=10):
        """Get most viewed articles."""
        from floor_app.operations.knowledge.models import Article

        return Article.objects.filter(
            status=Article.Status.PUBLISHED,
            is_deleted=False
        ).order_by('-view_count')[:limit]

    @staticmethod
    def get_articles_needing_review():
        """Get articles that need review."""
        from floor_app.operations.knowledge.models import Article

        today = timezone.now().date()
        return Article.objects.filter(
            review_due_date__lte=today,
            status__in=[Article.Status.PUBLISHED, Article.Status.APPROVED],
            is_deleted=False
        ).order_by('review_due_date')

    @staticmethod
    def get_expiring_articles(days=30):
        """Get articles expiring within specified days."""
        from floor_app.operations.knowledge.models import Article
        from datetime import timedelta

        cutoff = timezone.now().date() + timedelta(days=days)
        return Article.objects.filter(
            effective_until__lte=cutoff,
            effective_until__gte=timezone.now().date(),
            status=Article.Status.PUBLISHED,
            is_deleted=False
        ).order_by('effective_until')

    @staticmethod
    def get_category_tree():
        """Get hierarchical category structure."""
        from floor_app.operations.knowledge.models import Category

        root_categories = Category.objects.filter(
            parent__isnull=True,
            is_active=True,
            is_deleted=False
        ).prefetch_related('children').order_by('order')

        def build_tree(categories):
            tree = []
            for cat in categories:
                children = cat.children.filter(is_active=True, is_deleted=False).order_by('order')
                tree.append({
                    'category': cat,
                    'children': build_tree(children)
                })
            return tree

        return build_tree(root_categories)

    @staticmethod
    def get_article_stats():
        """Get overall article statistics."""
        from floor_app.operations.knowledge.models import Article

        qs = Article.objects.filter(is_deleted=False)

        return {
            'total': qs.count(),
            'published': qs.filter(status=Article.Status.PUBLISHED).count(),
            'draft': qs.filter(status=Article.Status.DRAFT).count(),
            'needs_review': KnowledgeService.get_articles_needing_review().count(),
            'by_type': qs.values('article_type').annotate(count=Count('id')),
        }

    @staticmethod
    def publish_article(article, user):
        """Publish an approved article."""
        from floor_app.operations.knowledge.models import Article

        if article.status != Article.Status.APPROVED:
            raise ValueError("Article must be approved before publishing")

        article.status = Article.Status.PUBLISHED
        article.published_at = timezone.now()
        article.updated_by = user
        article.save()

        return article

    @staticmethod
    def approve_article(article, user):
        """Approve an article for publishing."""
        from floor_app.operations.knowledge.models import Article

        article.status = Article.Status.APPROVED
        article.approved_by = user
        article.approved_at = timezone.now()
        article.updated_by = user
        article.save()

        return article
