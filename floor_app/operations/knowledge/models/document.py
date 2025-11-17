"""
Document model for file attachments and media management.
"""
import os
from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


def document_upload_path(instance, filename):
    """Generate upload path: media/knowledge/documents/YYYY/MM/filename"""
    from datetime import datetime
    now = datetime.now()
    return f"knowledge/documents/{now.year}/{now.month:02d}/{filename}"


class Document(AuditMixin, SoftDeleteMixin, PublicIdMixin, models.Model):
    """
    File storage for attachments, job aids, drawings, templates, etc.
    Can be attached to Articles, Instructions, Training Lessons, or any other model.
    """

    class FileType(models.TextChoices):
        PDF = 'PDF', 'PDF Document'
        IMAGE = 'IMAGE', 'Image'
        VIDEO = 'VIDEO', 'Video'
        AUDIO = 'AUDIO', 'Audio'
        SPREADSHEET = 'SPREADSHEET', 'Spreadsheet'
        DOCUMENT = 'DOCUMENT', 'Word Document'
        PRESENTATION = 'PRESENTATION', 'Presentation'
        ARCHIVE = 'ARCHIVE', 'Archive (ZIP/RAR)'
        CAD = 'CAD', 'CAD Drawing'
        OTHER = 'OTHER', 'Other'

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_path)
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER
    )
    description = models.TextField(blank=True)
    version = models.CharField(
        max_length=20,
        default='1.0',
        help_text="Document version number"
    )
    file_size = models.PositiveBigIntegerField(
        default=0,
        help_text="File size in bytes"
    )
    mime_type = models.CharField(max_length=100, blank=True)
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 checksum for integrity verification"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Publicly accessible without login"
    )
    download_count = models.PositiveIntegerField(default=0)

    # Optional metadata
    source_system = models.CharField(
        max_length=100,
        blank=True,
        help_text="Original source (e.g., 'Imported from SharePoint')"
    )
    external_url = models.URLField(
        blank=True,
        help_text="External link (for videos, external docs)"
    )

    # Expiry for time-sensitive documents
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Document expiry date (e.g., for certificates)"
    )

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file_type']),
            models.Index(fields=['is_public']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['public_id']),
        ]

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def save(self, *args, **kwargs):
        # Auto-detect file type from extension if not set
        if self.file and self.file_type == self.FileType.OTHER:
            ext = os.path.splitext(self.file.name)[1].lower()
            ext_map = {
                '.pdf': self.FileType.PDF,
                '.jpg': self.FileType.IMAGE,
                '.jpeg': self.FileType.IMAGE,
                '.png': self.FileType.IMAGE,
                '.gif': self.FileType.IMAGE,
                '.webp': self.FileType.IMAGE,
                '.svg': self.FileType.IMAGE,
                '.mp4': self.FileType.VIDEO,
                '.avi': self.FileType.VIDEO,
                '.mov': self.FileType.VIDEO,
                '.webm': self.FileType.VIDEO,
                '.mp3': self.FileType.AUDIO,
                '.wav': self.FileType.AUDIO,
                '.xlsx': self.FileType.SPREADSHEET,
                '.xls': self.FileType.SPREADSHEET,
                '.csv': self.FileType.SPREADSHEET,
                '.doc': self.FileType.DOCUMENT,
                '.docx': self.FileType.DOCUMENT,
                '.ppt': self.FileType.PRESENTATION,
                '.pptx': self.FileType.PRESENTATION,
                '.zip': self.FileType.ARCHIVE,
                '.rar': self.FileType.ARCHIVE,
                '.7z': self.FileType.ARCHIVE,
                '.dwg': self.FileType.CAD,
                '.dxf': self.FileType.CAD,
            }
            self.file_type = ext_map.get(ext, self.FileType.OTHER)

        # Calculate file size if file exists
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size

        super().save(*args, **kwargs)

    @property
    def filename(self):
        """Get just the filename without path"""
        if self.file:
            return os.path.basename(self.file.name)
        return ""

    @property
    def file_size_display(self):
        """Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def is_expired(self):
        """Check if document has expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

    def increment_download(self):
        """Increment download counter"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
