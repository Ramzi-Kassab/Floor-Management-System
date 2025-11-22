# Visual Planning Dashboard Implementation Guide

## Overview

The Visual Planning Dashboard provides a **drag-and-drop kanban-style board** showing all drill bits in work, their current workflow stage, assignments, and bottlenecks. This replaces Excel manual tracking with a live, interactive visual system.

**Key Features:**
- 📊 **Visual Workflow Board** - Drag-and-drop kanban with customizable stages
- 🎯 **Real-time WIP Tracking** - See all bits in system at a glance
- 🚦 **Bottleneck Detection** - Auto-highlight stages exceeding capacity
- ⏱️ **Time Tracking** - Track how long bits spend in each stage
- 👤 **Assignment Management** - Assign bits to team members
- 🔔 **Priority Flagging** - Mark urgent/rush jobs
- 📈 **Analytics Dashboard** - Trends, throughput, cycle time
- 💾 **Custom Views** - Save filtered board layouts

---

## Models Architecture

### 1. WorkflowStage
Configurable workflow stages (columns on kanban board).

**Example Stages:**
```
RECEIVED → INSPECTION → EVAL_QUEUE → EVALUATING → REPAIR_QUEUE →
REPAIRING → QC → READY_SHIP → SHIPPED
```

**Key Fields:**
- `stage_code` - Unique identifier (EVAL_QUEUE, REPAIRING)
- `stage_name` - Display name ("Evaluation Queue", "In Repair")
- `stage_type` - QUEUE, ACTIVE, INSPECTION, HOLD, COMPLETE
- `display_order` - Left-to-right position on board
- `color_hex` - Visual color for stage
- `capacity_limit` - Max bits allowed (null = unlimited)
- `warn_threshold` - Bottleneck warning level
- `average_duration_hours` - Expected time in stage
- `allowed_next_stages` - Valid transitions (drag targets)

### 2. BitWorkflowPosition
Tracks a bit's current position and full movement history.

**Key Fields:**
- `job_card` - Which job/bit
- `serial_unit` - Which serial number (if known)
- `stage` - Current or historical stage
- `entered_at` - When entered this stage
- `exited_at` - When left this stage (null if current)
- `is_current` - True if bit is currently here
- `assigned_to` - Who's working on it
- `is_on_hold` - Bit paused/blocked
- `is_priority` - Rush/expedite flag
- `board_column` / `board_row` - Visual position persistence

**Methods:**
- `move_to_stage()` - Transition to new stage (validates rules)
- `put_on_hold()` / `release_from_hold()` - Pause/resume
- `assign_to()` - Assign to user
- `time_in_stage` - How long in current stage
- `is_overdue` - Exceeds expected duration

### 3. VisualBoardLayout
Saved board views/filters for different users or purposes.

**Example Layouts:**
- "My Assigned Bits" - Only bits assigned to me
- "ENO Customer Jobs" - Filter by customer
- "Priority Rush Jobs" - Only priority bits
- "Bits Over 7 Days" - Age-based filter
- "Repair Workflow" - Only repair stages

**Key Fields:**
- `layout_name` - User-facing name
- `filter_rules` - JSON filter criteria
- `display_settings` - Visual preferences
- `visible_stages` - Which stages to show
- `is_shared` - Share with team

### 4. WIPDashboardMetrics
Periodic snapshots of WIP metrics for trending.

**Captured Metrics:**
- Total WIP count
- Count by stage
- Bottleneck stages
- Average age by stage
- Throughput (bits completed/added)

---

## Setup: Initial Configuration

### Step 1: Create Workflow Stages

```python
from floor_app.operations.planning.models import WorkflowStage

stages = [
    {
        'stage_code': 'RECEIVED',
        'stage_name': 'Received',
        'stage_type': 'QUEUE',
        'display_order': 10,
        'color_hex': '#95a5a6',
        'icon': 'fas fa-inbox',
        'capacity_limit': None,
        'warn_threshold': 50,
        'average_duration_hours': 4.0,
    },
    {
        'stage_code': 'INSPECTION',
        'stage_name': 'Initial Inspection',
        'stage_type': 'INSPECTION',
        'display_order': 20,
        'color_hex': '#3498db',
        'icon': 'fas fa-search',
        'capacity_limit': 10,
        'warn_threshold': 8,
        'average_duration_hours': 2.0,
    },
    {
        'stage_code': 'EVAL_QUEUE',
        'stage_name': 'Evaluation Queue',
        'stage_type': 'QUEUE',
        'display_order': 30,
        'color_hex': '#f39c12',
        'icon': 'fas fa-clock',
        'capacity_limit': None,
        'warn_threshold': 30,
        'average_duration_hours': 24.0,
    },
    {
        'stage_code': 'EVALUATING',
        'stage_name': 'Being Evaluated',
        'stage_type': 'ACTIVE',
        'display_order': 40,
        'color_hex': '#e67e22',
        'icon': 'fas fa-clipboard-check',
        'capacity_limit': 15,
        'warn_threshold': 12,
        'average_duration_hours': 8.0,
        'requires_assignment': True,
    },
    {
        'stage_code': 'REPAIR_QUEUE',
        'stage_name': 'Repair Queue',
        'stage_type': 'QUEUE',
        'display_order': 50,
        'color_hex': '#9b59b6',
        'icon': 'fas fa-tools',
        'capacity_limit': None,
        'warn_threshold': 40,
        'average_duration_hours': 48.0,
    },
    {
        'stage_code': 'REPAIRING',
        'stage_name': 'In Repair',
        'stage_type': 'ACTIVE',
        'display_order': 60,
        'color_hex': '#8e44ad',
        'icon': 'fas fa-wrench',
        'capacity_limit': 20,
        'warn_threshold': 18,
        'average_duration_hours': 16.0,
        'requires_assignment': True,
    },
    {
        'stage_code': 'QC',
        'stage_name': 'Quality Control',
        'stage_type': 'INSPECTION',
        'display_order': 70,
        'color_hex': '#27ae60',
        'icon': 'fas fa-check-double',
        'capacity_limit': 10,
        'warn_threshold': 8,
        'average_duration_hours': 4.0,
    },
    {
        'stage_code': 'READY_SHIP',
        'stage_name': 'Ready to Ship',
        'stage_type': 'QUEUE',
        'display_order': 80,
        'color_hex': '#2ecc71',
        'icon': 'fas fa-box',
        'capacity_limit': None,
        'warn_threshold': 20,
        'average_duration_hours': 12.0,
    },
    {
        'stage_code': 'SHIPPED',
        'stage_name': 'Shipped',
        'stage_type': 'COMPLETE',
        'display_order': 90,
        'color_hex': '#1abc9c',
        'icon': 'fas fa-shipping-fast',
        'is_terminal': True,
    },
    {
        'stage_code': 'ON_HOLD',
        'stage_name': 'On Hold',
        'stage_type': 'HOLD',
        'display_order': 100,
        'color_hex': '#e74c3c',
        'icon': 'fas fa-pause-circle',
    },
]

# Create stages and set up transitions
created_stages = {}
for stage_data in stages:
    stage, created = WorkflowStage.objects.get_or_create(
        stage_code=stage_data['stage_code'],
        defaults=stage_data
    )
    created_stages[stage_data['stage_code']] = stage

# Define allowed transitions
transitions = {
    'RECEIVED': ['INSPECTION'],
    'INSPECTION': ['EVAL_QUEUE', 'ON_HOLD'],
    'EVAL_QUEUE': ['EVALUATING'],
    'EVALUATING': ['REPAIR_QUEUE', 'READY_SHIP', 'ON_HOLD'],
    'REPAIR_QUEUE': ['REPAIRING'],
    'REPAIRING': ['QC', 'ON_HOLD'],
    'QC': ['READY_SHIP', 'REPAIRING', 'ON_HOLD'],  # Can send back to repair
    'READY_SHIP': ['SHIPPED'],
    'ON_HOLD': ['EVAL_QUEUE', 'REPAIR_QUEUE'],  # Can return to queue
}

for from_code, to_codes in transitions.items():
    from_stage = created_stages[from_code]
    for to_code in to_codes:
        to_stage = created_stages[to_code]
        from_stage.allowed_next_stages.add(to_stage)
```

### Step 2: Integration with JobCard Creation

Add to `floor_app/operations/production/models/job_card.py`:

```python
from floor_app.operations.planning.models import WorkflowStage, BitWorkflowPosition

class JobCard(models.Model):
    # ... existing fields ...

    def initialize_workflow(self):
        """
        Create initial workflow position when job card is created.
        Typically called in post_save signal or view.
        """
        # Get first stage (lowest display_order)
        first_stage = WorkflowStage.objects.filter(
            is_active=True
        ).order_by('display_order').first()

        if not first_stage:
            raise ValueError("No active workflow stages defined")

        # Create initial position
        position = BitWorkflowPosition.objects.create(
            job_card=self,
            serial_unit=self.serial_unit,  # If known
            stage=first_stage,
            entered_at=timezone.now(),
            is_current=True,
        )

        return position

    @property
    def current_workflow_position(self):
        """Get current workflow position."""
        return self.workflow_positions.filter(is_current=True).first()

    @property
    def current_stage(self):
        """Get current workflow stage."""
        pos = self.current_workflow_position
        return pos.stage if pos else None

    def workflow_history(self):
        """Get full workflow history ordered by time."""
        return self.workflow_positions.order_by('entered_at')
```

**Signal to auto-create workflow position:**

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=JobCard)
def create_workflow_position(sender, instance, created, **kwargs):
    """Auto-create workflow position when job card is created."""
    if created:
        instance.initialize_workflow()
```

---

## Front-End Implementation

### HTML Structure

```html
<!-- templates/planning/visual_board.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/visual-board.css' %}">
<style>
.workflow-board {
    display: flex;
    gap: 20px;
    padding: 20px;
    overflow-x: auto;
    min-height: 70vh;
}

.stage-column {
    background: #f8f9fa;
    border-radius: 8px;
    min-width: 300px;
    max-width: 350px;
    display: flex;
    flex-direction: column;
}

.stage-header {
    padding: 15px;
    border-radius: 8px 8px 0 0;
    color: white;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stage-count {
    background: rgba(255, 255, 255, 0.3);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.9em;
}

.stage-body {
    padding: 10px;
    flex: 1;
    overflow-y: auto;
    min-height: 200px;
}

.bit-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 10px;
    cursor: move;
    transition: all 0.2s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.bit-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transform: translateY(-2px);
}

.bit-card.dragging {
    opacity: 0.5;
}

.bit-card.priority {
    border-left: 4px solid #e74c3c;
}

.bit-card.on-hold {
    background: #fff3cd;
    border-color: #ffc107;
}

.bit-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.job-number {
    font-weight: bold;
    color: #2c3e50;
}

.bit-badges {
    display: flex;
    gap: 4px;
}

.bit-info {
    font-size: 0.85em;
    color: #6c757d;
    margin-bottom: 4px;
}

.bit-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #e9ecef;
    font-size: 0.8em;
}

.time-in-stage {
    color: #6c757d;
}

.time-in-stage.exceeding {
    color: #e74c3c;
    font-weight: bold;
}

.assigned-user {
    background: #e9ecef;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.85em;
}

.stage-column.at-capacity .stage-header {
    background: repeating-linear-gradient(
        45deg,
        #e74c3c,
        #e74c3c 10px,
        #c0392b 10px,
        #c0392b 20px
    );
}

.stage-column.bottleneck .stage-header {
    box-shadow: 0 0 0 3px #ffc107;
}
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Board Header -->
    <div class="board-header">
        <h2>
            <i class="fas fa-th-large"></i> Visual Planning Board
        </h2>

        <div class="board-controls">
            <!-- View Selector -->
            <select id="board-layout" class="form-select" style="width: 200px;">
                <option value="">All Bits (Default)</option>
                {% for layout in saved_layouts %}
                <option value="{{ layout.id }}">{{ layout.layout_name }}</option>
                {% endfor %}
            </select>

            <!-- Filters -->
            <button class="btn btn-outline-primary" data-bs-toggle="modal" data-bs-target="#filterModal">
                <i class="fas fa-filter"></i> Filters
            </button>

            <!-- Refresh -->
            <button class="btn btn-outline-secondary" onclick="refreshBoard()">
                <i class="fas fa-sync-alt"></i> Refresh
            </button>

            <!-- Save View -->
            <button class="btn btn-outline-success" onclick="saveCurrentView()">
                <i class="fas fa-save"></i> Save View
            </button>
        </div>
    </div>

    <!-- Summary Stats -->
    <div class="summary-stats">
        <div class="stat-card">
            <span class="stat-value">{{ total_wip }}</span>
            <span class="stat-label">Total WIP</span>
        </div>
        <div class="stat-card">
            <span class="stat-value">{{ total_priority }}</span>
            <span class="stat-label">Priority</span>
        </div>
        <div class="stat-card">
            <span class="stat-value">{{ total_on_hold }}</span>
            <span class="stat-label">On Hold</span>
        </div>
        <div class="stat-card">
            <span class="stat-value">{{ avg_cycle_time }}</span>
            <span class="stat-label">Avg Cycle Time (hrs)</span>
        </div>
    </div>

    <!-- Kanban Board -->
    <div class="workflow-board" id="workflowBoard">
        {% for stage in stages %}
        <div class="stage-column {% if stage.is_at_capacity %}at-capacity{% endif %} {% if stage.is_bottleneck %}bottleneck{% endif %}"
             data-stage-id="{{ stage.id }}"
             data-stage-code="{{ stage.stage_code }}">

            <!-- Stage Header -->
            <div class="stage-header" style="background-color: {{ stage.color_hex }};">
                <div>
                    <i class="{{ stage.icon }}"></i>
                    {{ stage.stage_name }}
                </div>
                <span class="stage-count">
                    {{ stage.get_current_count }}
                    {% if stage.capacity_limit %}
                        / {{ stage.capacity_limit }}
                    {% endif %}
                </span>
            </div>

            <!-- Stage Body (Drop Zone) -->
            <div class="stage-body"
                 data-stage-id="{{ stage.id }}"
                 ondrop="drop(event)"
                 ondragover="allowDrop(event)"
                 ondragleave="dragLeave(event)">

                {% for position in stage.bit_positions.all %}
                {% if position.is_current %}
                <div class="bit-card {% if position.is_priority %}priority{% endif %} {% if position.is_on_hold %}on-hold{% endif %}"
                     draggable="true"
                     ondragstart="drag(event)"
                     data-position-id="{{ position.id }}"
                     data-job-card-id="{{ position.job_card.id }}">

                    <!-- Card Header -->
                    <div class="bit-card-header">
                        <span class="job-number">{{ position.job_card.job_card_number }}</span>
                        <div class="bit-badges">
                            {% if position.is_priority %}
                            <span class="badge bg-danger">RUSH</span>
                            {% endif %}
                            {% if position.is_on_hold %}
                            <span class="badge bg-warning">HOLD</span>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Card Info -->
                    <div class="bit-info">
                        <i class="fas fa-user"></i> {{ position.job_card.customer_name|truncatechars:15 }}
                    </div>
                    {% if position.serial_unit %}
                    <div class="bit-info">
                        <i class="fas fa-barcode"></i> {{ position.serial_unit.serial_number }}
                    </div>
                    {% endif %}
                    <div class="bit-info">
                        <i class="fas fa-tag"></i> {{ position.job_card.get_job_type_display }}
                    </div>

                    <!-- Card Footer -->
                    <div class="bit-footer">
                        <span class="time-in-stage {% if position.is_exceeding_average %}exceeding{% endif %}">
                            <i class="fas fa-clock"></i> {{ position.time_in_stage_hours }}h
                        </span>
                        {% if position.assigned_to %}
                        <span class="assigned-user">
                            <i class="fas fa-user-circle"></i> {{ position.assigned_to.username }}
                        </span>
                        {% endif %}
                    </div>
                </div>
                {% endif %}
                {% endfor %}

            </div>
        </div>
        {% endfor %}
    </div>
</div>

<!-- Bit Detail Modal -->
<div class="modal fade" id="bitDetailModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Bit Details</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="bitDetailContent">
                <!-- Loaded via AJAX -->
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/visual-board.js' %}"></script>
<script>
// Drag and Drop Implementation
let draggedElement = null;

function allowDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add('drop-zone-active');
}

function dragLeave(ev) {
    ev.currentTarget.classList.remove('drop-zone-active');
}

function drag(ev) {
    draggedElement = ev.target;
    ev.target.classList.add('dragging');
    ev.dataTransfer.setData("position_id", ev.target.dataset.positionId);
}

function drop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drop-zone-active');

    const positionId = ev.dataTransfer.getData("position_id");
    const targetStageId = ev.currentTarget.dataset.stageId;

    // Call API to move bit
    moveBitToStage(positionId, targetStageId);

    if (draggedElement) {
        draggedElement.classList.remove('dragging');
    }
}

async function moveBitToStage(positionId, targetStageId) {
    try {
        const response = await fetch(`/api/planning/workflow-positions/${positionId}/move/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                target_stage_id: targetStageId
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Refresh board
            location.reload();
        } else {
            alert(`Error: ${data.error}`);
            location.reload();
        }
    } catch (error) {
        console.error('Error moving bit:', error);
        alert('Failed to move bit');
        location.reload();
    }
}

function refreshBoard() {
    location.reload();
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Click on card to show details
document.querySelectorAll('.bit-card').forEach(card => {
    card.addEventListener('dblclick', function(e) {
        if (!e.target.classList.contains('btn')) {
            const jobCardId = this.dataset.jobCardId;
            showBitDetails(jobCardId);
        }
    });
});

function showBitDetails(jobCardId) {
    // Load bit details via AJAX
    fetch(`/api/production/job-cards/${jobCardId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('bitDetailContent').innerHTML = renderBitDetails(data);
            new bootstrap.Modal(document.getElementById('bitDetailModal')).show();
        });
}
</script>
{% endblock %}
```

### View Implementation

```python
# floor_app/operations/planning/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from floor_app.operations.planning.models import (
    WorkflowStage,
    BitWorkflowPosition,
    VisualBoardLayout
)

class VisualPlanningBoardView(LoginRequiredMixin, TemplateView):
    template_name = 'planning/visual_board.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all active stages
        stages = WorkflowStage.objects.filter(
            is_active=True
        ).prefetch_related(
            'bit_positions__job_card',
            'bit_positions__serial_unit',
            'bit_positions__assigned_to'
        ).order_by('display_order')

        # Get user's saved layouts
        saved_layouts = VisualBoardLayout.objects.filter(
            created_by=self.request.user
        ) | VisualBoardLayout.objects.filter(
            is_shared=True
        )

        # Calculate summary stats
        current_positions = BitWorkflowPosition.objects.filter(is_current=True)
        total_wip = current_positions.count()
        total_priority = current_positions.filter(is_priority=True).count()
        total_on_hold = current_positions.filter(is_on_hold=True).count()

        # Average cycle time
        avg_cycle = current_positions.aggregate(
            avg_hours=models.Avg('time_in_stage_hours')
        )['avg_hours'] or 0

        context.update({
            'stages': stages,
            'saved_layouts': saved_layouts,
            'total_wip': total_wip,
            'total_priority': total_priority,
            'total_on_hold': total_on_hold,
            'avg_cycle_time': round(avg_cycle, 1),
        })

        return context
```

### API Endpoints (Django REST Framework)

```python
# floor_app/operations/planning/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from floor_app.operations.planning.models import (
    WorkflowStage,
    BitWorkflowPosition,
    VisualBoardLayout
)

class BitWorkflowPositionViewSet(viewsets.ModelViewSet):
    queryset = BitWorkflowPosition.objects.all()
    serializer_class = BitWorkflowPositionSerializer

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """
        Move bit to a new stage.

        POST /api/planning/workflow-positions/{id}/move/
        {
            "target_stage_id": 5,
            "notes": "Customer approved quotation",
            "assigned_to": 3  // Optional user ID
        }
        """
        position = self.get_object()
        target_stage_id = request.data.get('target_stage_id')

        if not target_stage_id:
            return Response(
                {'error': 'target_stage_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_stage = WorkflowStage.objects.get(id=target_stage_id)
        except WorkflowStage.DoesNotExist:
            return Response(
                {'error': 'Invalid target stage'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get assigned user if provided
        assigned_to = None
        if request.data.get('assigned_to'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                assigned_to = User.objects.get(id=request.data['assigned_to'])
            except User.DoesNotExist:
                pass

        # Move bit
        try:
            new_position = position.move_to_stage(
                new_stage=target_stage,
                user=request.user,
                notes=request.data.get('notes', ''),
                assigned_to=assigned_to
            )

            return Response(
                self.get_serializer(new_position).data,
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def hold(self, request, pk=None):
        """Put bit on hold"""
        position = self.get_object()
        reason = request.data.get('reason', 'No reason provided')

        position.put_on_hold(reason=reason, user=request.user)

        return Response(self.get_serializer(position).data)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        """Release bit from hold"""
        position = self.get_object()
        position.release_from_hold(user=request.user)

        return Response(self.get_serializer(position).data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign bit to user"""
        position = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            position.assign_to(user)
            return Response(self.get_serializer(position).data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid user'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def toggle_priority(self, request, pk=None):
        """Toggle priority flag"""
        position = self.get_object()
        is_priority = request.data.get('is_priority', not position.is_priority)

        position.mark_priority(is_priority)

        return Response(self.get_serializer(position).data)


class WIPDashboardMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for WIP metrics (for analytics charts).
    """
    queryset = WIPDashboardMetrics.objects.all()
    serializer_class = WIPDashboardMetricsSerializer

    @action(detail=False, methods=['post'])
    def capture(self, request):
        """
        Manually trigger metrics capture.
        Normally called from scheduled task.
        """
        from floor_app.operations.planning.models import WIPDashboardMetrics

        snapshot = WIPDashboardMetrics.capture_snapshot()

        return Response(
            self.get_serializer(snapshot).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def trend(self, request):
        """
        Get trend data for analytics dashboard.

        GET /api/planning/wip-metrics/trend/?days=30
        """
        from datetime import timedelta
        from django.utils import timezone

        days = int(request.query_params.get('days', 7))
        cutoff = timezone.now() - timedelta(days=days)

        metrics = self.queryset.filter(
            snapshot_date__gte=cutoff
        ).order_by('snapshot_date')

        return Response(self.get_serializer(metrics, many=True).data)
```

---

## Analytics Dashboard

### Trend Charts (Chart.js)

```html
<!-- templates/planning/analytics_dashboard.html -->
<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">WIP Trend (Last 30 Days)</div>
            <div class="card-body">
                <canvas id="wipTrendChart"></canvas>
            </div>
        </div>
    </div>

    <div class="col-md-6">
        <div class="card">
            <div class="card-header">Stage Distribution</div>
            <div class="card-body">
                <canvas id="stageDistributionChart"></canvas>
            </div>
        </div>
    </div>
</div>

<script>
// WIP Trend Line Chart
fetch('/api/planning/wip-metrics/trend/?days=30')
    .then(res => res.json())
    .then(data => {
        const ctx = document.getElementById('wipTrendChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => new Date(d.snapshot_date).toLocaleDateString()),
                datasets: [{
                    label: 'Total WIP',
                    data: data.map(d => d.total_wip),
                    borderColor: '#3498db',
                    tension: 0.1
                }, {
                    label: 'On Hold',
                    data: data.map(d => d.total_on_hold),
                    borderColor: '#e74c3c',
                    tension: 0.1
                }, {
                    label: 'Priority',
                    data: data.map(d => d.total_priority),
                    borderColor: '#f39c12',
                    tension: 0.1
                }]
            }
        });
    });

// Stage Distribution Pie Chart
const latestMetrics = await fetch('/api/planning/wip-metrics/').then(r => r.json());
const latest = latestMetrics[0];

const ctx2 = document.getElementById('stageDistributionChart').getContext('2d');
new Chart(ctx2, {
    type: 'pie',
    data: {
        labels: Object.keys(latest.stage_counts),
        datasets: [{
            data: Object.values(latest.stage_counts),
            backgroundColor: [
                '#3498db', '#e67e22', '#9b59b6', '#2ecc71',
                '#e74c3c', '#f39c12', '#1abc9c', '#34495e'
            ]
        }]
    }
});
</script>
```

---

## Scheduled Tasks (Celery)

### Periodic Metrics Capture

```python
# floor_app/tasks.py
from celery import shared_task
from floor_app.operations.planning.models import WIPDashboardMetrics

@shared_task
def capture_wip_metrics():
    """
    Capture WIP metrics snapshot.
    Run hourly via Celery Beat.
    """
    snapshot = WIPDashboardMetrics.capture_snapshot()
    return f"Captured WIP metrics: {snapshot.total_wip} bits"


# In celeryconfig.py
from celery.schedules import crontab

beat_schedule = {
    'capture-wip-metrics-hourly': {
        'task': 'floor_app.tasks.capture_wip_metrics',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
}
```

---

## Admin Integration

```python
# floor_app/operations/planning/admin.py
from django.contrib import admin
from floor_app.operations.planning.models import (
    WorkflowStage,
    BitWorkflowPosition,
    VisualBoardLayout,
    WIPDashboardMetrics,
)

@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = [
        'stage_code', 'stage_name', 'stage_type', 'display_order',
        'get_current_count', 'capacity_limit', 'is_active'
    ]
    list_filter = ['stage_type', 'is_active', 'is_terminal']
    search_fields = ['stage_code', 'stage_name']
    ordering = ['display_order']

@admin.register(BitWorkflowPosition)
class BitWorkflowPositionAdmin(admin.ModelAdmin):
    list_display = [
        'job_card', 'stage', 'is_current', 'entered_at',
        'time_in_stage_hours', 'assigned_to', 'is_priority', 'is_on_hold'
    ]
    list_filter = [
        'stage', 'is_current', 'is_priority', 'is_on_hold',
        'entered_at', 'assigned_to'
    ]
    search_fields = [
        'job_card__job_card_number',
        'serial_unit__serial_number'
    ]
    readonly_fields = ['entered_at', 'exited_at', 'time_in_stage_hours']

@admin.register(VisualBoardLayout)
class VisualBoardLayoutAdmin(admin.ModelAdmin):
    list_display = [
        'layout_name', 'created_by', 'is_shared', 'is_default'
    ]
    list_filter = ['is_shared', 'is_default', 'created_by']
    search_fields = ['layout_name', 'description']
    filter_horizontal = ['visible_stages', 'shared_with_users']

@admin.register(WIPDashboardMetrics)
class WIPDashboardMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'snapshot_date', 'total_wip', 'total_priority', 'total_on_hold',
        'completed_since_last', 'new_since_last'
    ]
    list_filter = ['snapshot_date']
    readonly_fields = [
        'snapshot_date', 'total_wip', 'stage_counts',
        'average_age_by_stage', 'bottleneck_stages'
    ]
```

---

## URL Configuration

```python
# floor_app/operations/planning/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VisualPlanningBoardView
from .api.views import BitWorkflowPositionViewSet, WIPDashboardMetricsViewSet

router = DefaultRouter()
router.register('workflow-positions', BitWorkflowPositionViewSet)
router.register('wip-metrics', WIPDashboardMetricsViewSet)

urlpatterns = [
    # Visual board view
    path('board/', VisualPlanningBoardView.as_view(), name='visual-board'),

    # API
    path('api/', include(router.urls)),
]
```

---

## Summary

The Visual Planning Dashboard provides:

✅ **Drag-and-Drop Kanban** - Move bits between stages visually
✅ **Real-Time WIP Tracking** - See all bits in system at a glance
✅ **Bottleneck Detection** - Auto-highlight overloaded stages
✅ **Time Tracking** - Monitor how long bits spend in each stage
✅ **Assignment Management** - Assign bits to team members
✅ **Priority Flagging** - Mark urgent/rush jobs
✅ **Custom Views** - Save filtered board layouts
✅ **Analytics Dashboard** - Trends, throughput, cycle time metrics
✅ **Mobile Responsive** - Works on tablets and phones
✅ **Audit Trail** - Full movement history for each bit

### Key Benefits:

1. **Replaces Excel manual tracking** with live visual system
2. **Reduces bottlenecks** through real-time visibility
3. **Improves throughput** with better work allocation
4. **Enhances accountability** via assignment and time tracking
5. **Enables data-driven decisions** through analytics

### Next Steps:

1. Run migrations
2. Create workflow stages
3. Wire up job card creation to initialize workflow
4. Build front-end board page
5. Configure API endpoints
6. Set up periodic metrics capture
7. Train team on drag-and-drop workflow
