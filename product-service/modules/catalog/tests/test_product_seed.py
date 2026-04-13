from django.test import SimpleTestCase

from ..seeds.products_seed import PRODUCT_SEED


class ProductSeedContractTest(SimpleTestCase):
    def test_product_seed_is_large_enough_for_plan_three(self):
        self.assertGreaterEqual(len(PRODUCT_SEED), 50)

    def test_product_seed_has_unique_slugs(self):
        slugs = [product["slug"] for product in PRODUCT_SEED]
        self.assertEqual(len(slugs), len(set(slugs)))
