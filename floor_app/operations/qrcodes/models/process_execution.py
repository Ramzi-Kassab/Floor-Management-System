"""
Process Execution models for tracking production step state machine.

Handles: Start/End/Pause/Resume logic with time tracking.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from floor_app.mixins import AuditMixin


class ProcessExecutionStatus:
    """Status constants for process execution state machine."""
    NOT_STARTED = 'NOT_STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    PAUSED = 'PAUSED'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    BLOCKED = 'BLOCKED'

    CHOICES = (
        (NOT_STARTED, 'Not Started'),
        (IN_PROGRESS, 'In Progress'),
        (PAUSED, 'Paused'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
        (BLOCKED, 'Blocked'),
    )


class ProcessExecutionManager(models.Manager):
    """Custom manager for ProcessExecution."""

    def active(self):
        """Get executions that are currently active (in progress or paused)."""
        return self.filter(status__in=[
            ProcessExecutionStatus.IN_PROGRESS,
            ProcessExecutionStatus.PAUSED
        ])

    def in_progress(self):
        """Get executions currently in progress."""
        return self.filter(status=ProcessExecutionStatus.IN_PROGRESS)

    def completed(self):
        """Get completed executions."""
        return self.filter(status=ProcessExecutionStatus.COMPLETED)

    def for_job_card(self, job_card_id):
        """Get executions for a specific job card."""
        return self.filter(job_card_id=job_card_id)

    def for_operator(self, employee_id):
        """Get executions by a specific operator."""
        return self.filter(operator_employee_id=employee_id)


class ProcessExecution(AuditMixin):
    """
    Tracks execution of a single process step.

    State machine:
    - NOT_STARTED -> IN_PROGRESS (scan to start)
    - IN_PROGRESS -> COMPLETED (scan to end)
    - IN_PROGRESS -> PAUSED (scan to pause)
    - PAUSED -> IN_PROGRESS (scan to resume)
    - Any -> CANCELLED (manual cancellation)
    - Any -> BLOCKED (failed validation)
    """

    # Link to Job Card (production module)
    job_card_id = models.BigIntegerField(
        db_index=True,
        help_text="ID of JobCard this execution belongs to"
    )

    # Link to Route Step (production module)
    route_step_id = models.BigIntegerField(
        db_index=True,
        help_text="ID of JobRouteStep being executed"
    )

    # Operation details (cached for reporting)
    operation_code = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Operation code (cached)"
    )
    operation_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Operation name (cached)"
    )
    sequence_number = models.IntegerField(
        default=0,
        help_text="Sequence in route (cached)"
    )

    # Who executed
    operator_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_executions',
        help_text="User who executed this step"
    )
    operator_employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="HR Employee ID of operator"
    )
    operator_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Operator name at execution time"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ProcessExecutionStatus.CHOICES,
        default=ProcessExecutionStatus.NOT_STARTED,
        db_index=True,
        help_text="Current execution status"
    )

    # Time tracking
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When execution started"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When execution ended"
    )

    # Pause tracking
    total_pause_minutes = models.IntegerField(
        default=0,
        help_text="Total minutes spent in paused state"
    )
    pause_count = models.IntegerField(
        default=0,
        help_text="Number of times paused"
    )

    # Work center / station
    work_center = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Work center or station code"
    )
    work_center_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Work center name"
    )

    # QR Code used to track this execution
    qcode_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="QCode ID used for this process step"
    )

    # Notes and results
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Operator notes"
    )

    completion_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes at completion"
    )

    # Quality / defects
    defects_found = models.IntegerField(
        default=0,
        help_text="Number of defects found during this step"
    )
    defect_notes = models.TextField(
        blank=True,
        default="",
        help_text="Details of defects"
    )

    # Measurements / outputs (generic JSON for flexibility)
    measurements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Step measurements as JSON"
    )

    objects = ProcessExecutionManager()

    class Meta:
        db_table = 'qrcode_process_execution'
        verbose_name = 'Process Execution'
        verbose_name_plural = 'Process Executions'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['job_card_id'], name='ix_procexec_jobcard'),
            models.Index(fields=['route_step_id'], name='ix_procexec_step'),
            models.Index(fields=['status'], name='ix_procexec_status'),
            models.Index(fields=['operator_employee_id'], name='ix_procexec_operator'),
            models.Index(fields=['-start_time'], name='ix_procexec_start'),
            models.Index(fields=['qcode_id'], name='ix_procexec_qcode'),
        ]

    def __str__(self):
        return f"{self.operation_name} - {self.get_status_display()}"

    @property
    def duration_minutes(self):
        """Calculate total duration in minutes (excluding pauses)."""
        if not self.start_time:
            return 0

        end = self.end_time or timezone.now()
        total = (end - self.start_time).total_seconds() / 60
        return max(0, total - self.total_pause_minutes)

    @property
    def is_active(self):
        """Check if execution is currently active."""
        return self.status in [
            ProcessExecutionStatus.IN_PROGRESS,
            ProcessExecutionStatus.PAUSED
        ]

    def start(self, user=None, employee_id=None, operator_name="", work_center=""):
        """
        Start the process execution.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.status != ProcessExecutionStatus.NOT_STARTED:
            return False, f"Cannot start: current status is {self.get_status_display()}"

        self.status = ProcessExecutionStatus.IN_PROGRESS
        self.start_time = timezone.now()
        self.operator_user = user
        self.operator_employee_id = employee_id
        self.operator_name = operator_name
        self.work_center = work_center
        self.save()

        return True, f"Started {self.operation_name}"

    def end(self, completion_notes=""):
        """
        End the process execution.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.status != ProcessExecutionStatus.IN_PROGRESS:
            if self.status == ProcessExecutionStatus.PAUSED:
                return False, "Cannot end while paused. Resume first."
            return False, f"Cannot end: current status is {self.get_status_display()}"

        self.status = ProcessExecutionStatus.COMPLETED
        self.end_time = timezone.now()
        self.completion_notes = completion_notes
        self.save()

        return True, f"Completed {self.operation_name} in {self.duration_minutes:.1f} minutes"

    def pause(self, reason=""):
        """
        Pause the process execution.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.status != ProcessExecutionStatus.IN_PROGRESS:
            return False, f"Cannot pause: current status is {self.get_status_display()}"

        # Create pause record
        ProcessPause.objects.create(
            execution=self,
            pause_start=timezone.now(),
            reason=reason
        )

        self.status = ProcessExecutionStatus.PAUSED
        self.pause_count += 1
        self.save()

        return True, f"Paused {self.operation_name}"

    def resume(self):
        """
        Resume the process execution from pause.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.status != ProcessExecutionStatus.PAUSED:
            return False, f"Cannot resume: current status is {self.get_status_display()}"

        # End current pause
        current_pause = self.pauses.filter(pause_end__isnull=True).first()
        if current_pause:
            current_pause.pause_end = timezone.now()
            current_pause.save()

            # Update total pause time
            pause_duration = (current_pause.pause_end - current_pause.pause_start).total_seconds() / 60
            self.total_pause_minutes += int(pause_duration)

        self.status = ProcessExecutionStatus.IN_PROGRESS
        self.save()

        return True, f"Resumed {self.operation_name}"

    def cancel(self, reason=""):
        """Cancel the execution."""
        if self.status == ProcessExecutionStatus.COMPLETED:
            return False, "Cannot cancel a completed execution"

        self.status = ProcessExecutionStatus.CANCELLED
        self.notes += f"\nCancelled: {reason}"
        self.save()

        return True, f"Cancelled {self.operation_name}"


class ProcessPause(models.Model):
    """
    Tracks individual pause periods within a process execution.
    """

    execution = models.ForeignKey(
        ProcessExecution,
        on_delete=models.CASCADE,
        related_name='pauses',
        help_text="Process execution this pause belongs to"
    )

    pause_start = models.DateTimeField(
        default=timezone.now,
        help_text="When pause started"
    )

    pause_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When pause ended (null if still paused)"
    )

    reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for pause"
    )

    class Meta:
        db_table = 'qrcode_process_pause'
        verbose_name = 'Process Pause'
        verbose_name_plural = 'Process Pauses'
        ordering = ['-pause_start']
        indexes = [
            models.Index(fields=['execution'], name='ix_procpause_exec'),
            models.Index(fields=['-pause_start'], name='ix_procpause_start'),
        ]

    def __str__(self):
        duration = self.duration_minutes
        if duration:
            return f"Pause for {duration:.1f} minutes"
        return "Active pause"

    @property
    def duration_minutes(self):
        """Calculate pause duration in minutes."""
        if not self.pause_end:
            return None
        return (self.pause_end - self.pause_start).total_seconds() / 60
