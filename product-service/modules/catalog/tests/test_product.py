from decimal import Decimal

from django.test import SimpleTestCase

from ..application.commands.create_product import CreateProductCommand


class CreateProductCommandTest(SimpleTestCase):
    def test_create_product_command_keeps_attributes(self):
        command = CreateProductCommand(
            name="Demo product",
            base_price=Decimal("100.00"),
            attributes={"ram": "16GB"},
        )
        self.assertEqual(command.attributes["ram"], "16GB")
