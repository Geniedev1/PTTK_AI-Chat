from django.test import SimpleTestCase

from ..domain.entities.category import Category


class CategoryEntityTest(SimpleTestCase):
    def test_category_can_have_parent(self):
        category = Category(id=1, name="Laptop", slug="laptop", parent_id=None)
        self.assertEqual(category.slug, "laptop")
