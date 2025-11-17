# floor_app/operations/knowledge/models/__init__.py
"""
Knowledge & Instructions Module - Models
"""

# Core models
from .category import Category
from .tag import Tag
from .document import Document

# Knowledge articles
from .article import (
    Article,
    ArticleAttachment,
    ArticleAcknowledgment,
)

# FAQ
from .faq import FAQGroup, FAQEntry

# Rule Engine (Powerful Instructions System)
from .instruction import (
    InstructionRule,
    RuleCondition,
    RuleAction,
    InstructionTargetScope,
    InstructionExecutionLog,
)

# Training Center
from .training import (
    TrainingCourse,
    TrainingLesson,
    TrainingEnrollment,
    TrainingLessonProgress,
    TrainingSchedule,
    TrainingScheduleRegistration,
)

__all__ = [
    # Core
    'Category',
    'Tag',
    'Document',
    # Articles
    'Article',
    'ArticleAttachment',
    'ArticleAcknowledgment',
    # FAQ
    'FAQGroup',
    'FAQEntry',
    # Instructions/Rules
    'InstructionRule',
    'RuleCondition',
    'RuleAction',
    'InstructionTargetScope',
    'InstructionExecutionLog',
    # Training
    'TrainingCourse',
    'TrainingLesson',
    'TrainingEnrollment',
    'TrainingLessonProgress',
    'TrainingSchedule',
    'TrainingScheduleRegistration',
]
