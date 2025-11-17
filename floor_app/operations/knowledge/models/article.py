"""
Article model - core knowledge content entity.
Handles procedures, guidelines, FAQs, policies, checklists, etc.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .category import Category
from .tag import Tag
from .document import Document


class Article(AuditMixin, SoftDeleteMixin, PublicIdMixin, models.Model):
    """
    Central knowledge article for all types of documentation.
    This is the single source of truth for procedures, guidelines, policies, etc.
    """

    class ArticleType(models.TextChoices):
        PROCEDURE = 'PROCEDURE', 'Procedure'
        WORK_INSTRUCTION = 'WORK_INSTRUCTION', 'Work Instruction'
        GUIDELINE = 'GUIDELINE', 'Guideline'
        POLICY = 'POLICY', 'Policy'
        FAQ = 'FAQ', 'FAQ'
        CHECKLIST = 'CHECKLIST', 'Checklist'
        TEMPLATE = 'TEMPLATE', 'Template'
        REFERENCE = 'REFERENCE', 'Reference Document'
        SAFETY = 'SAFETY', 'Safety Document'
        QUALITY = 'QUALITY', 'Quality Document'
        TECHNICAL = 'TECHNICAL', 'Technical Specification'
        TRAINING = 'TRAINING', 'Training Material'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        APPROVED = 'APPROVED', 'Approved'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'
        SUPERSEDED = 'SUPERSEDED', 'Superseded'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    # Core fields
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique article code, e.g., 'PROC-QC-001'"
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    title = models.CharField(max_length=255)
    summary = models.TextField(
        blank=True,
        help_text="Short description/abstract"
    )
    body = models.TextField(
        help_text="Main content (supports HTML/Markdown)"
    )

    # Classification
    article_type = models.CharField(
        max_length=20,
        choices=ArticleType.choices,
        default=ArticleType.REFERENCE
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )

    # Organization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='articles'
    )
    owner_department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knowledge_articles'
    )

    # Attachments
    attachments = models.ManyToManyField(
        Document,
        through='ArticleAttachment',
        blank=True,
        related_name='articles'
    )

    # Versioning
    version = models.CharField(
        max_length=20,
        default='1.0',
        help_text="Article version"
    )
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newer_versions',
        help_text="Link to previous version of this article"
    )
    change_summary = models.TextField(
        blank=True,
        help_text="Summary of changes in this version"
    )

    # Workflow
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_articles'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_articles'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Validity
    effective_from = models.DateField(
        null=True,
        blank=True,
        help_text="Date article becomes effective"
    )
    effective_until = models.DateField(
        null=True,
        blank=True,
        help_text="Date article expires (if applicable)"
    )
    review_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date for next review"
    )

    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(
        default=False,
        help_text="Show in featured/important section"
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pin to top of lists"
    )

    # Related articles
    related_articles = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text="Related knowledge articles"
    )

    # Access control
    requires_acknowledgment = models.BooleanField(
        default=False,
        help_text="Users must acknowledge reading this"
    )
    restricted_to_departments = models.ManyToManyField(
        'hr.Department',
        blank=True,
        related_name='restricted_articles',
        help_text="Only these departments can view (empty = all)"
    )
    restricted_to_positions = models.ManyToManyField(
        'hr.Position',
        blank=True,
        related_name='restricted_articles',
        help_text="Only these positions can view (empty = all)"
    )

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['-is_pinned', '-is_featured', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['slug']),
            models.Index(fields=['article_type', 'status']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['owner_department', 'status']),
            models.Index(fields=['is_featured', 'is_pinned']),
            models.Index(fields=['review_due_date']),
            models.Index(fields=['public_id']),
        ]
        permissions = [
            ('can_publish_article', 'Can publish articles'),
            ('can_approve_article', 'Can approve articles'),
            ('can_review_article', 'Can review articles'),
        ]

    def __str__(self):
        return f"{self.code}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.code}-{self.title}")[:255]
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Article.all_objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug[:250]}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def increment_view(self):
        """Increment view counter"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    @property
    def is_current(self):
        """Check if article is currently valid"""
        from django.utils import timezone
        today = timezone.now().date()
        if self.effective_from and today < self.effective_from:
            return False
        if self.effective_until and today > self.effective_until:
            return False
        return self.status == self.Status.PUBLISHED

    @property
    def needs_review(self):
        """Check if article needs review"""
        if self.review_due_date:
            from django.utils import timezone
            return timezone.now().date() >= self.review_due_date
        return False

    @property
    def all_versions(self):
        """Get all versions of this article (including this one)"""
        versions = [self]
        current = self.previous_version
        while current:
            versions.append(current)
            current = current.previous_version
        return versions

    def create_new_version(self, new_body, change_summary, user=None):
        """Create a new version of this article"""
        # Increment version
        parts = self.version.split('.')
        if len(parts) >= 2:
            new_version = f"{parts[0]}.{int(parts[1]) + 1}"
        else:
            new_version = f"{self.version}.1"

        # Create new article as new version
        new_article = Article.objects.create(
            code=self.code,
            slug=f"{self.slug}-v{new_version.replace('.', '-')}",
            title=self.title,
            summary=self.summary,
            body=new_body,
            article_type=self.article_type,
            status=Article.Status.DRAFT,
            priority=self.priority,
            category=self.category,
            owner_department=self.owner_department,
            version=new_version,
            previous_version=self,
            change_summary=change_summary,
            created_by=user,
        )

        # Copy tags
        new_article.tags.set(self.tags.all())

        # Mark old version as superseded
        self.status = Article.Status.SUPERSEDED
        self.save(update_fields=['status'])

        return new_article


class ArticleAttachment(models.Model):
    """
    Through model for Article-Document relationship.
    Adds context about how the document is used.
    """

    class UsageType(models.TextChoices):
        REFERENCE = 'REFERENCE', 'Reference'
        JOB_AID = 'JOB_AID', 'Job Aid'
        TEMPLATE = 'TEMPLATE', 'Template'
        DRAWING = 'DRAWING', 'Technical Drawing'
        FORM = 'FORM', 'Form'
        CHECKLIST = 'CHECKLIST', 'Checklist'
        EXAMPLE = 'EXAMPLE', 'Example'
        OTHER = 'OTHER', 'Other'

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='article_attachments'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='article_usages'
    )
    usage_type = models.CharField(
        max_length=20,
        choices=UsageType.choices,
        default=UsageType.REFERENCE
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional caption for this attachment"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Article Attachment'
        verbose_name_plural = 'Article Attachments'
        ordering = ['order', 'id']
        unique_together = [['article', 'document']]

    def __str__(self):
        return f"{self.article.code} - {self.document.title}"


class ArticleAcknowledgment(models.Model):
    """
    Track user acknowledgments of important articles.
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='acknowledgments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_acknowledgments'
    )
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Article Acknowledgment'
        verbose_name_plural = 'Article Acknowledgments'
        unique_together = [['article', 'user']]
        indexes = [
            models.Index(fields=['article', 'acknowledged_at']),
        ]

    def __str__(self):
        return f"{self.user} acknowledged {self.article.code}"
