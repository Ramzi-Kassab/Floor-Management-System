"""
Tag model for flexible tagging of knowledge content.
"""
from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
    """
    Simple tagging system for knowledge articles and instructions.
    Examples: PDC, LSTK, ARAMCO, Safety, Urgent, Critical
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    color = models.CharField(
        max_length=7,
        default='#6b7280',
        help_text="Hex color for tag display"
    )
    is_system = models.BooleanField(
        default=False,
        help_text="System tags cannot be deleted"
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def article_count(self):
        """Count of articles using this tag"""
        return self.articles.count()
