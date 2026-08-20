# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(product.id, found_product.id)
        self.assertEqual(product.name, found_product.name)
        self.assertEqual(product.description, found_product.description)
        self.assertEqual(product.price, found_product.price)
        self.assertEqual(product.available, found_product.available)
        self.assertEqual(product.category, found_product.category)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change it and save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a product"""
        product = ProductFactory()
        product.create()
        # Check if the product was created
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        # Check that the only created product was deleted
        # and the list is empty
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        # Check if there are no products at all
        self.assertEqual(len(Product.all()), 0)
        # Creates 5 products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we got back 5 products
        self.assertEqual(len(Product.all()), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        # Creates a dictionary to "pre-group" and count
        # products by name
        qty = {}
        for product in products:
            product.create()
            if product.name in qty:
                qty[product.name] = qty[product.name] + 1
            else:
                qty[product.name] = 1
        # Uses the dictionary to check the number of each
        # distinct product by name
        for key, value in qty.items():
            found = Product.find_by_name(key)
            self.assertEqual(found.count(), value)
            for product in found:
                self.assertEqual(product.name, key)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.price = 50
            product.create()
        found_products = Product.find_by_price(50)
        self.assertEqual(found_products.count(), 10)
        found_products_by_str_price = Product.find_by_price("50.00")
        self.assertEqual(found_products_by_str_price.count(), 10)

    def test_serialize(self):
        """It should get Serialized properly"""
        product = ProductFactory()
        serialized_product = product.serialize()
        self.assertEqual(product.id, serialized_product["id"])
        self.assertEqual(product.name, serialized_product["name"])
        self.assertEqual(product.description, serialized_product["description"])
        self.assertEqual(str(product.price), serialized_product["price"])
        self.assertEqual(product.available, serialized_product["available"])
        self.assertEqual(product.category.name, serialized_product["category"])

    def test_deserialize(self):
        """It should get Deserialized properly"""
        product = ProductFactory()
        target_product = ProductFactory()
        target_product.deserialize(product.serialize())
        self.assertEqual(product.name, target_product.name)
        self.assertEqual(product.description, target_product.description)
        self.assertEqual(product.price, target_product.price)
        self.assertEqual(product.available, target_product.available)
        self.assertEqual(product.category, target_product.category)

    def test_deserialize_available_error(self):
        """It should raise an error when deserializing non-bool available"""
        product = ProductFactory()
        tempered_product = product.serialize()
        tempered_product["available"] = "RandomText"
        target_product = ProductFactory()
        self.assertRaises(
            DataValidationError,
            target_product.deserialize,
            tempered_product)

    def test_deserialize_missing_prop_error(self):
        """It should raise an error when missing properties"""
        product = ProductFactory()
        tempered_product = product.serialize()
        del tempered_product["name"]
        target_product = ProductFactory()
        self.assertRaises(
            DataValidationError,
            target_product.deserialize,
            tempered_product)

    def test_deserialize_category_error(self):
        """It should raise an error when deserializing invalid category"""
        product = ProductFactory()
        tempered_product = product.serialize()
        tempered_product["category"] = "ThisIsNotAValidCategory"
        target_product = ProductFactory()
        self.assertRaises(
            DataValidationError,
            target_product.deserialize,
            tempered_product)

    def test_deserialize_null_error(self):
        """It should raise an error when deserializing null product"""
        target_product = ProductFactory()
        self.assertRaises(
            DataValidationError,
            target_product.deserialize,
            None)

    def test_update_null_id_error(self):
        """It should raise an error when updating product with null id"""
        product = ProductFactory()
        product.create()
        product.id = None
        self.assertRaises(
            DataValidationError,
            product.update)
