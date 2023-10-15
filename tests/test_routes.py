######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
    nosetests --stop tests/test_routes.py
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_get_product(self):
        """It should Get a single Product"""
        # get an id
        test_product = self._create_products(1)[0]
        logging.debug("Product for Reading: %s", test_product)
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        logging.debug("data= %s", data)
        self.assertEqual(data["name"], test_product.name)

    def test_get_product_not_found(self):
        """It should not find a product without id"""
        response = self.client.get(f"{BASE_URL}/{0}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_product(self):
        """It should Put a single Product"""
        # get an id
        test_product = self._create_products(1)[0]
        logging.debug("Product for Updating: %s", test_product)
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # change something
        test_product.name = "new_name"
        logging.debug("Test Product after changing: %s", test_product.serialize())
        # save it
        response = self.client.put(f"{BASE_URL}/{test_product.id}", json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check if changes were saved
        logging.debug("Test Product after saving: %s", test_product.serialize())
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data2 = response.get_json()
        # self.assertEqual(data2["name"], "new_name")

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_product(self):
        """It should Delete a single Product"""
        # create product and get an id
        products = self._create_products(1)
        test_product = products[0]
        logging.debug("Product for Deleting: %s, products=%s, products:\n%s", test_product, len(products), products)
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(products), 1)
        # delete the product
        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        logging.debug("Product deleted: %s, products=%s", test_product, len(products))
        # check that it's gone
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_not_existing_product(self):
        """It should nothing happen when deleting unexisting product"""
        response = self.client.delete(f"{BASE_URL}/{0}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # TEST LIST ALL
    # ----------------------------------------------------------
    def test_list_all_products(self):
        """It should list all Products"""
        # create products
        numbers = 5
        products = self._create_products(numbers)
        logging.debug(f"products created for List All: %s", products)
        self.assertEqual(len(products), numbers)
        # test get
        response = self.client.get(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        logging.debug(f"response data: %s", data)
        # test number of products
        self.assertEqual(len(data), numbers)
        # test values
        for i in range(numbers):
            self.assertEqual(data[i]["name"], products[i].name)
            self.assertEqual(data[i]["id"], products[i].id)
            self.assertEqual(data[i]["description"], products[i].description)
            self.assertEqual(Decimal(data[i]["price"]), products[i].price)
            self.assertEqual(data[i]["available"], products[i].available)
            self.assertEqual(data[i]["category"], products[i].category.name)

    # ----------------------------------------------------------
    # TEST LIST BY NAME
    # ----------------------------------------------------------
    def test_list_products_by_name(self):
        """It should list all Products with given name"""
        # create products
        numbers = 15
        test_products = self._create_products(numbers)
        logging.debug(f"%s products created for List By Name: %s", len(test_products), test_products)
        self.assertEqual(len(test_products), numbers)
        # get a name
        test_filter = test_products[0].name
        logging.debug(f"test_name= %s", test_filter)
        filtered_products = [product for product in test_products if product.name == test_filter]
        # test get
        response = self.client.get(BASE_URL, json={"name": test_filter})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        logging.debug(f"response data: %s", data)
        data_filtered = [prod for prod in data if prod["name"] == test_filter]
        # test number of selected products
        self.assertEqual(len(data_filtered), len(filtered_products))
        # test values
        for i in range(len(filtered_products)):
            self.assertEqual(data_filtered[i]["name"], filtered_products[i].name)
            self.assertEqual(data_filtered[i]["id"], filtered_products[i].id)
            self.assertEqual(data_filtered[i]["description"], filtered_products[i].description)
            self.assertEqual(Decimal(data_filtered[i]["price"]), filtered_products[i].price)
            self.assertEqual(data_filtered[i]["available"], filtered_products[i].available)
            self.assertEqual(data_filtered[i]["category"], filtered_products[i].category.name)

    # ----------------------------------------------------------
    # TEST LIST BY CATEGORY
    # ----------------------------------------------------------
    def test_list_products_by_category(self):
        """It should list all Products with given category"""
        # create products
        numbers = 15
        test_products = self._create_products(numbers)
        logging.debug(f"%s products created for List By Category: %s", len(test_products), test_products)
        self.assertEqual(len(test_products), numbers)
        # get a category
        test_filter = test_products[0].category
        logging.debug(f"test_category= %s", test_filter)
        filtered_products = [product for product in test_products if product.category == test_filter]
        # test get
        response = self.client.get(BASE_URL, json={"category": test_filter})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        logging.debug(f"response data: %s", data)
        data_filtered = [prod for prod in data if prod["category"] == test_filter]
        # test number of selected products
        self.assertEqual(len(data_filtered), len(filtered_products))
        # test values
        for i in range(len(filtered_products)):
            self.assertEqual(data_filtered[i]["name"], filtered_products[i].name)
            self.assertEqual(data_filtered[i]["id"], filtered_products[i].id)
            self.assertEqual(data_filtered[i]["description"], filtered_products[i].description)
            self.assertEqual(Decimal(data_filtered[i]["price"]), filtered_products[i].price)
            self.assertEqual(data_filtered[i]["available"], filtered_products[i].available)
            self.assertEqual(data_filtered[i]["category"], filtered_products[i].category.name)