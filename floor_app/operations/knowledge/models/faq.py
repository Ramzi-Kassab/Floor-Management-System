"""
FAQ models for frequently asked questions management.
"""
from django.db import models
from floor_app.mixins import AuditMixin, SoftDeleteMixin
from .category import Category


class FAQGroup(AuditMixin, SoftDeleteMixin, models.Model):
    """
    Group/category for organizing FAQs.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faq_groups'
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bootstrap icon class"
    )

    class Meta:
        verbose_name = 'FAQ Group'
        verbose_name_plural = 'FAQ Groups'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def active_entries_count(self):
        return self.entries.filter(is_deleted=False, is_published=True).count()


class FAQEntry(AuditMixin, SoftDeleteMixin, models.Model):
    """
    Individual FAQ question and answer.
    """
    group = models.ForeignKey(
        FAQGroup,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    question = models.TextField()
    answer = models.TextField(help_text="Supports HTML/Markdown")
    short_answer = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief answer for quick display"
    )

    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(
        default=False,
        help_text="Show in featured/popular FAQs"
    )

    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)

    # Keywords for search
    keywords = models.TextField(
        blank=True,
        help_text="Keywords for better search (comma-separated)"
    )

    class Meta:
        verbose_name = 'FAQ Entry'
        verbose_name_plural = 'FAQ Entries'
        ordering = ['group', 'order', '-is_featured']
        indexes = [
            models.Index(fields=['group', 'is_published']),
            models.Index(fields=['is_featured', 'is_published']),
        ]

    def __str__(self):
        return f"{self.group.name}: {self.question[:50]}"

    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def mark_helpful(self, helpful=True):
        if helpful:
            self.helpful_count += 1
        else:
            self.not_helpful_count += 1
        self.save(update_fields=['helpful_count', 'not_helpful_count'])

    @property
    def helpfulness_score(self):
        """Percentage of helpful ratings"""
        total = self.helpful_count + self.not_helpful_count
        if total > 0:
            return (self.helpful_count / total) * 100
        return 0
