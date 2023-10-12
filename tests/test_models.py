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
logger = logging.getLogger("flask.app")


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

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Read a product from the database"""
        # produce product and store it in db
        product = ProductFactory()
        logger.info("Create for Reading: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.available,
                    product.category)
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # gets product from db
        product_found = Product.find(product.id)
        self.assertTrue(product_found.id, product.id)
        self.assertTrue(product_found.name, product.name)
        self.assertTrue(product_found.description, product.description)
        self.assertTrue(product_found.price, product.price)
        # self.assertTrue(product_found.available, product.available)
        # self.assertTrue(product_found.category, product.category)

    def test_update_a_product(self):
        """It should Update a product in the database"""
        # produce product and store it in db
        product = ProductFactory()
        logger.info("Create for Updating: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.available,
                    product.category)
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # update and save product
        product.description = "new description string"
        original_id = product.id
        logger.info("Read before Updating: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.available,
                    product.category)
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "new description string")
        logger.info("Read after Updating: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.available,
                    product.category)
        # read the updated product (same id, new description)
        # should be the only product
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "new description string")
        
    def test_invalid_id_on_update(self):
        """test invalid ID on update"""
        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """It should Delete a product in the database"""
        # produce product and store it in db
        product = ProductFactory()
        logger.info("Create for Deleting: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.available,
                    product.category)
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # count: it should be the only one
        self.assertEqual(len(Product.all()), 1)
        products = Product.all()
        self.assertEqual(products[0].id, product.id)
        self.assertEqual(products[0].name, product.name)
        product.delete()
        # count again (or again 'products = Product.all()' for refresh)
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all products of the database"""
        # be sure db is empty
        products = Product.all()
        self.assertEqual(products, [])
        # produce products and store them in db
        for _ in range(5):
            product = ProductFactory()
            logger.info("Create for Listing: \nproduct id= %s, \nname= %s, \
                \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                        product.id,
                        product.name,
                        product.description,
                        product.price,
                        product.available,
                        product.category)
            product.id = None
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_product_by_name(self):
        """It should find all product with this name"""
        # produce products
        products_n = ProductFactory.create_batch(5)
        # store them in db
        for product in products_n:
            logger.info("Create for Find by Name: \nproduct id= %s, \nname= %s, \
                \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                        product.id,
                        product.name,
                        product.description,
                        product.price,
                        product.available,
                        product.category)
            product.id = None
            product.create()
        self.assertEqual(len(products_n), 5)
        # find first name and count its occurrence
        name0 = products_n[0].name
        name_count = len([product for product in products_n if product.name == name0])
        logger.info("name = %s, count = %s", name0, name_count)
        products_with_name0 = Product.find_by_name(name0)
        # count the found products (len() doesn't work because it's a query!)
        self.assertEqual(products_with_name0.count(), name_count)
        # check that found products have the right name
        for _ in products_with_name0:
            self.assertEqual(_.name, name0)

    def test_find_product_by_category(self):
        """It should find all products in a category"""
        # produce products
        products_c = ProductFactory.create_batch(15)
        # store them in db
        for product in products_c:
            logger.info("Create for Find By Category: \nproduct id= %s, \nname= %s, \
                \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                        product.id,
                        product.name,
                        product.description,
                        product.price,
                        product.available,
                        product.category)
            product.id = None
            product.create()
        self.assertEqual(len(products_c), 15)
        # read first category and count its occurrence
        category0 = products_c[0].category
        category_count = len([product for product in products_c if product.category == category0])
        logger.info("category = %s, count = %s", category0, category_count)
        # find products by this category
        found = Product.find_by_category(category0)
        # count the found products
        self.assertEqual(found.count(), category_count)
        # check that found products are in the right category
        for _ in found:
            self.assertEqual(_.category, category0)

    def test_find_product_by_availability(self):
        """It should find all availabe products"""
        # produce products
        products_a = ProductFactory.create_batch(10)
        # store them in db
        for product in products_a:
            logger.info("Create for Find By Availibility: \nproduct id= %s, \nname= %s, \
                \ndescription= %s, \nprice= %2f, \navailable= %s, \ncategory= %s\n",
                        product.id,
                        product.name,
                        product.description,
                        product.price,
                        product.available,
                        product.category)
            product.id = None
            product.create()
        self.assertEqual(len(products_a), 10)
        # read first category and count its occurrence
        availability0 = products_a[0].available
        # count products with this availability
        count = len([product for product in products_a if product.available == availability0])
        logger.info("availability = %s, count = %s", availability0, count)
        # find products with this availability
        found = Product.find_by_availability(availability0)
        # count the found products
        self.assertEqual(found.count(), count)
        # check that found products are in the right availability
        for _ in found:
            self.assertEqual(_.available, availability0)

    def test_find_product_by_price(self):
        """It should find all products with this price"""
        # produce products
        products_p = ProductFactory.create_batch(5)
        # store them in db
        for product in products_p:
            logger.info("Create for Find By Availibility: \nproduct id= %s, \nname= %s, \
                \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                        product.id,
                        product.name,
                        product.description,
                        product.price,
                        product.available,
                        product.category)
            product.id = None
            product.create()
        self.assertEqual(len(products_p), 5)

        # read first price and count its occurrence
        price0float = products_p[0].price
        # count products with this price
        count = len([product for product in products_p if product.price == price0float])
        logger.info("price = %2f, count = %s", price0float, count)
        # find products with this price
        found = Product.find_by_price(price0float)
        # count the found products
        self.assertEqual(found.count(), count)
        # check that found products have the right price
        for _ in found:
            self.assertEqual(Decimal(_.price), price0float)

    def test_find_product_by_price_as_string(self):
        """It should find all products with this price"""
        # produce products
        products_ps = ProductFactory.create_batch(5)
        # store them in db
        for product in products_ps:
            logger.info("Create for Find By Availibility: \nproduct id= %s, \nname= %s, \
                \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                        product.id,
                        product.name,
                        product.description,
                        product.price,
                        product.available,
                        product.category)
            product.id = None
            product.create()
        self.assertEqual(len(products_ps), 5)
        price0float = products_ps[0].price
        count = len([product for product in products_ps if product.price == price0float])
        # handle string-exception
        price0string = str(products_ps[0].price)
        logger.info("price = %s", price0string)
        # find products with this price
        found = Product.find_by_price(price0string)
        # count the found products
        self.assertEqual(found.count(), count)
        # check that found products have the right price
        for _ in found:
            self.assertEqual(Decimal(_.price), Decimal(price0string))

    def test_serialize(self):
        """Product should be stored in dictionary"""
        product = ProductFactory()
        logger.info("Create for Serializing: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.available,
                    product.category)
        dictionary = product.serialize()
        self.assertEqual(dictionary['id'], product.id)
        self.assertEqual(dictionary['name'], product.name)
        self.assertEqual(dictionary['description'], product.description)
        self.assertEqual(dictionary['price'], str(product.price))
        self.assertEqual(dictionary['available'], product.available)
        self.assertEqual(dictionary['category'], product.category.name)

    def test_deserialize(self):
        """Product should be read from dictionary"""
        # create product
        product = ProductFactory()
        logger.info("Create for Deserializing: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %s, \navailable= %s, \ncategory= %s\n",
                    product.id,
                    product.name,
                    product.description,
                    product.price,
                    product.available,
                    product.category)
        # store it in dictionary
        dictionary_d = product.serialize()
        logger.info("dictionary category = %s", dictionary_d['category'])
        # self.assertEqual(dictionary_d['id'], product.id)
        self.assertEqual(dictionary_d['name'], product.name)
        self.assertEqual(dictionary_d['description'], product.description)
        self.assertEqual(dictionary_d['price'], str(product.price))
        self.assertEqual(dictionary_d['available'], product.available)
        self.assertEqual(dictionary_d['category'], product.category.name)
        # read dictionary and store it in product-instance
        new_product = Product()
        new_product.deserialize(dictionary_d)
        logger.info("Read from Dictionary: \nproduct id= %s, \nname= %s, \
            \ndescription= %s, \nprice= %2f, \navailable= %s, \ncategory= %s\n",
                    new_product.id,
                    new_product.name,
                    new_product.description,
                    new_product.price,
                    new_product.available,
                    new_product.category)
        # self.assertEqual(new_product.id, dictionary_d['id'])
        self.assertEqual(new_product.name, dictionary_d['name'])
        self.assertEqual(new_product.description, dictionary_d['description'])
        self.assertEqual(new_product.price, Decimal(dictionary_d['price']))
        self.assertEqual(new_product.available, dictionary_d['available'])
        self.assertEqual(new_product.category.name, dictionary_d['category'])

    def test_invalid_availability_on_deserialize(self):
        """Test Invalid Availability on deserialize"""
        product = ProductFactory()
        dictionary_foo = product.serialize()
        dictionary_foo["available"] = "something else"
        new_product = Product()
        self.assertRaises(DataValidationError, new_product.deserialize, dictionary_foo)

    def test_invalid_dictionary_on_deserialize(self):
        """Test Invalid Dictionary on deserialize"""
        dictionary = ["I'm not a dictionary", 42]
        new_product = Product()
        self.assertRaises(DataValidationError, new_product.deserialize, dictionary)

    def test_invalid_key_on_deserialize(self):
        """Test Invalid Dictionary Key on deserialize"""
        product = Product()
        product = ProductFactory()
        dictionary_bar = product.serialize()
        dictionary_bar.pop("price")
        new_product = Product()
        self.assertRaises(DataValidationError, new_product.deserialize, dictionary_bar)
