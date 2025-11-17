"""
Category model for organizing knowledge articles and documents.
Supports hierarchical structure with parent-child relationships.
"""
from django.db import models
from django.utils.text import slugify
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class Category(AuditMixin, SoftDeleteMixin, models.Model):
    """
    Hierarchical category for organizing knowledge content.
    Examples: Safety, Quality, Production, HR Policies, Technical Procedures
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bootstrap icon class, e.g., 'bi-gear-fill'"
    )
    color = models.CharField(
        max_length=7,
        default='#6366f1',
        help_text="Hex color code for category badge"
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Category.all_objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def full_path(self):
        """Get full category path (e.g., 'Safety > PPE > Gloves')"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def depth(self):
        """Get depth level in hierarchy"""
        if self.parent:
            return self.parent.depth + 1
        return 0

    def get_ancestors(self):
        """Get all parent categories up to root"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all child categories recursively"""
        descendants = list(self.children.filter(is_deleted=False))
        for child in self.children.filter(is_deleted=False):
            descendants.extend(child.get_descendants())
        return descendants
