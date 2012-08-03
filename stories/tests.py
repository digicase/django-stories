import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from stories.models import Story
from stories.models import COMMENTS_FROZEN, COMMENTS_ENABLED, COMMENTS_DISABLED

class BaseTests(TestCase):
    fixtures = ['auth.json', 'profile.json', 'stories.json']
    def setUp(self):
        self.story1 = Story.objects.get(pk=1)
        self.story2 = Story.objects.get(pk=2)


class StoryTests(BaseTests):
    def test_comments(self):
        self.assertFalse(self.story1.comments_frozen)
        self.story1.comment_status = COMMENTS_DISABLED
        self.story1.save()

        self.assertFalse(self.story1.comments_frozen)

        self.story1.comment_status = COMMENTS_FROZEN
        self.story1.save()

        self.assertTrue(self.story1.comments_frozen)

    def test_author(self):
        self.assertEqual(self.story1.author,
            '<a href="/people/1">John Doe</a> and '\
            '<a href="/people/3">Mark Moe</a>')

    def test_author_display(self):
        ad = self.story1.author_display
        ad = ad.replace('\n', '')
        self.assertEqual(ad,
            '<a href="/users/John/">John Doe</a> and '\
            '<a href="/users/Mark/">Mark Moe</a>')

    def test_paragraphs(self):
        self.assertEqual(len(self.story1.paragraphs), 3)

    def test_published(self):
        # Should be two total stories
        self.assertEqual(len(Story.objects.all()), 2)
        # Only one of these is marked as published
        self.assertEqual(len(Story.published.all()), 1)


class RelationTests(BaseTests):
    fixtures = ['auth.json', 'profile.json', 'videos.json',
                'photos.json', 'stories.json']

    def setUp(self):
        super(RelationTests, self).setUp()
        from simpleapp.models import BasicPhoto, BasicVideo
        self.photo1 = BasicPhoto.objects.get(pk=1)
        self.photo1 = BasicPhoto.objects.get(pk=2)
        self.video1 = BasicVideo.objects.get(pk=1)
        self.video2 = BasicVideo.objects.get(pk=2)

        self.photo_ctype = ContentType.objects.get_for_model(BasicPhoto)
        self.video_ctype = ContentType.objects.get_for_model(BasicVideo)

    def test_has_relation_attrs(self):
        self.assertTrue(hasattr(self.story1, 'get_related_content_type'))
        self.assertTrue(hasattr(self.story1, 'get_relation_type'))

    def test_add_relations(self):
        from stories.models import StoryRelation
        rel1, created = StoryRelation.objects.get_or_create(
            story=self.story1,
            content_type=self.photo_ctype, object_id=1)
        self.assertTrue(created)

    def test_related_methods(self):
        from stories.models import StoryRelation
        rel1 = StoryRelation.objects.create(
            story=self.story1,
            content_type=self.photo_ctype, object_id=1)

        items = self.story1.get_related_content_type('basic photo')
        manager_items = StoryRelation.objects.get_content_type('basic photo')
        self.assertEqual(list(items), [rel1])
        self.assertEqual(list(manager_items), [rel1])

        rel2 = StoryRelation.objects.create(
            story=self.story2,
            content_type=self.video_ctype, object_id=1,
            relation_type="Regular")

        items = self.story2.get_relation_type("Regular")
        manager_items = StoryRelation.objects.get_relation_type('Regular')
        self.assertEqual(list(items), [rel2])
        self.assertEqual(list(manager_items), [rel2])


class PrintTests(BaseTests):
    def test_has_fields(self):
        self.assertTrue(hasattr(self.story1, 'print_pub_date'))
        self.assertTrue(hasattr(self.story1, 'print_section'))
        self.assertTrue(hasattr(self.story1, 'print_page'))

    def test_saving(self):
        date = datetime.datetime.now()
        self.story1.print_pub_date = date
        self.story1.print_section = 'feature'
        self.story1.print_page = '1a'
        self.story1.save()

        self.assertEqual(self.story1.print_pub_date, date)
        self.assertEqual(self.story1.print_section, 'feature')
        self.assertEqual(self.story1.print_page, '1a')


class CategoryTests(BaseTests):
    fixtures = ['auth.json', 'profile.json',
                'categories.json', 'stories_with_cats.json']

    def setUp(self):
        super(CategoryTests, self).setUp()
        from categories.models import Category

        self.cat1 = Category.objects.get(pk=1)
        self.cat2 = Category.objects.get(pk=2)
        self.cat3 = Category.objects.get(pk=3)

    def test_has_fields(self):
        from categories.fields import CategoryM2MField, CategoryFKField

        self.assertTrue(hasattr(self.story1, 'primary_category'))
        self.assertTrue(hasattr(self.story1, 'categories'))

        self.assertEqual(
            Story._meta.get_field('primary_category').__class__,
            CategoryFKField)

        self.assertEqual(
            Story._meta.get_field('categories').__class__,
            CategoryM2MField)

    def test_field_data(self):
        self.assertEqual(self.story1.primary_category, self.cat1)

        s1_cat_ids = [c.pk for c in self.story1.categories.all()]
        s2_cat_ids = [c.pk for c in self.story2.categories.all()]

        self.assertTrue(self.cat2.pk in s1_cat_ids)
        self.assertTrue(self.cat3.pk in s1_cat_ids)

        self.assertTrue(self.cat2.pk in s2_cat_ids)
        self.assertFalse(self.cat3.pk in s2_cat_ids)