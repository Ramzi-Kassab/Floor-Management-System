"""
Basic tests for Knowledge & Instructions module models.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from ..models import (
    Category, Tag, Document, Article, ArticleAttachment,
    InstructionRule, RuleCondition, RuleAction,
    TrainingCourse, TrainingLesson,
)


class CategoryModelTest(TestCase):
    def test_create_category(self):
        category = Category.objects.create(
            name='Quality',
            description='Quality control procedures'
        )
        self.assertEqual(category.name, 'Quality')
        self.assertIsNotNone(category.slug)
        self.assertEqual(category.depth, 0)

    def test_nested_category(self):
        parent = Category.objects.create(name='Safety')
        child = Category.objects.create(name='PPE', parent=parent)
        self.assertEqual(child.depth, 1)
        self.assertEqual(child.full_path, 'Safety > PPE')


class TagModelTest(TestCase):
    def test_create_tag(self):
        tag = Tag.objects.create(name='Urgent')
        self.assertEqual(tag.name, 'Urgent')
        self.assertIsNotNone(tag.slug)


class ArticleModelTest(TestCase):
    def test_create_article(self):
        article = Article.objects.create(
            code='PROC-001',
            title='Test Procedure',
            summary='Test summary',
            body='Test body content',
            article_type=Article.ArticleType.PROCEDURE,
            status=Article.Status.DRAFT,
        )
        self.assertEqual(article.code, 'PROC-001')
        self.assertIsNotNone(article.slug)
        self.assertIsNotNone(article.public_id)

    def test_article_increment_view(self):
        article = Article.objects.create(
            code='PROC-002',
            title='Test',
            body='Body'
        )
        initial_count = article.view_count
        article.increment_view()
        self.assertEqual(article.view_count, initial_count + 1)


class InstructionRuleModelTest(TestCase):
    def test_create_instruction(self):
        instruction = InstructionRule.objects.create(
            code='INS-001',
            title='Test Instruction',
            description='Test description',
            instruction_type=InstructionRule.InstructionType.TECHNICAL,
            priority=InstructionRule.Priority.HIGH,
            status=InstructionRule.Status.DRAFT,
        )
        self.assertEqual(instruction.code, 'INS-001')
        self.assertIsNotNone(instruction.public_id)
        self.assertTrue(instruction.is_default)

    def test_instruction_validity(self):
        from django.utils import timezone
        from datetime import timedelta

        # Active instruction
        instruction = InstructionRule.objects.create(
            code='INS-002',
            title='Active',
            description='Active instruction',
            status=InstructionRule.Status.ACTIVE,
            is_temporary=False,
        )
        self.assertTrue(instruction.is_valid_now)

        # Expired instruction
        expired = InstructionRule.objects.create(
            code='INS-003',
            title='Expired',
            description='Expired instruction',
            status=InstructionRule.Status.ACTIVE,
            is_temporary=True,
            valid_until=timezone.now() - timedelta(days=1),
        )
        self.assertFalse(expired.is_valid_now)


class RuleConditionModelTest(TestCase):
    def test_create_condition(self):
        instruction = InstructionRule.objects.create(
            code='INS-COND',
            title='Test',
            description='Test'
        )
        ct = ContentType.objects.get_for_model(User)
        condition = RuleCondition.objects.create(
            instruction=instruction,
            target_model=ct,
            field_path='username',
            operator=RuleCondition.Operator.EQUALS,
            value='"admin"',
        )
        self.assertEqual(condition.operator, 'EQUALS')

    def test_evaluate_condition(self):
        instruction = InstructionRule.objects.create(
            code='INS-EVAL',
            title='Test Eval',
            description='Test'
        )
        ct = ContentType.objects.get_for_model(User)
        condition = RuleCondition.objects.create(
            instruction=instruction,
            target_model=ct,
            field_path='username',
            operator=RuleCondition.Operator.EQUALS,
            value='"testuser"',
        )

        user = User(username='testuser')
        context = {ct.id: user}
        result = condition.evaluate(context)
        self.assertTrue(result)


class RuleActionModelTest(TestCase):
    def test_create_action(self):
        instruction = InstructionRule.objects.create(
            code='INS-ACT',
            title='Test Action',
            description='Test'
        )
        action = RuleAction.objects.create(
            instruction=instruction,
            action_type=RuleAction.ActionType.SHOW_MESSAGE,
            message_template='Test message for {username}',
            severity='info',
        )
        self.assertEqual(action.action_type, 'SHOW_MESSAGE')


class TrainingCourseModelTest(TestCase):
    def test_create_course(self):
        course = TrainingCourse.objects.create(
            code='TR-001',
            title='Safety Training',
            description='Basic safety training',
            course_type=TrainingCourse.CourseType.SAFETY,
            estimated_duration_minutes=60,
        )
        self.assertEqual(course.code, 'TR-001')
        self.assertEqual(course.duration_display, '1h 0m')
        self.assertIsNotNone(course.public_id)

    def test_course_completion_rate(self):
        course = TrainingCourse.objects.create(
            code='TR-002',
            title='Test Course',
            description='Test'
        )
        # Initially 0% completion
        self.assertEqual(course.completion_rate, 0)


class TrainingLessonModelTest(TestCase):
    def test_create_lesson(self):
        course = TrainingCourse.objects.create(
            code='TR-003',
            title='Test Course',
            description='Test'
        )
        lesson = TrainingLesson.objects.create(
            course=course,
            sequence=1,
            title='Introduction',
            lesson_type=TrainingLesson.LessonType.READING,
            content='Lesson content here',
        )
        self.assertEqual(lesson.title, 'Introduction')
        self.assertTrue(lesson.is_mandatory)
