import json
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch
import pandas as pd

from dbtool import DBTool

DEFAULT_JSON = {
    "database_name": "test_db",
    "table_name": "test_table",
    "directory": "imagine/",
    "file_identifier": "puppy",
    "height": 480,
    "width": 480,
    "inference_steps": 20,
    "seed": "78901427222289238",
    "primary_key": "7592f4b7-7d16-4009-b09f-2c1ad220423f",
    "file_type": "png"
}

class TestDBTool(unittest.TestCase):

    def setUp(self):
        self.db_tool = DBTool(database_name="test_db", table_name="test_table")

    def test_get(self):
        self.db_tool.delete_table("test_table")
        self.db_tool.json2dbtool("primary_key", "default.json")
        result = self.db_tool.get(primary_key="7592f4b7-7d16-4009-b09f-2c1ad220423f", column_name="file_identifier")
        self.assertEqual(result, "puppy", "Get command.")

    def test_put(self):
        result = self.db_tool.put("7592f4b7-7d16-4009-b09f-2c1ad220423f", element_key="seed", value="78901427222289238")
        self.assertEqual(result, 1, "***** uuid matched to first record")

    def test_to_pickle(self):
        self.db_tool.to_pickle("test_pickle.pkl")

    def test_update_value(self):
        result = self.db_tool.put("test_key", "test_column", "new_value")
        self.assertEqual(result, 2, "New record: test_key, column 2.")

    def test_get_column(self):
        result = self.db_tool.get_column("primary_key")
        self.assertIsNotNone(result, "Get column failed.")

    def test_get_columns(self):
        result = self.db_tool.get_columns(exclude_2_keys=True)
        self.assertIsNotNone(result, "Get columns failed.")

    def test_get_values(self):
        result = self.db_tool.get_values("7592f4b7-7d16-4009-b09f-2c1ad220423f")
        self.assertIsNotNone(result, "Get values failed.")

    def test_delete_database(self):
        self.db_tool.delete_database("test_db")

    def test_delete_table(self):
        self.db_tool.delete_table("test_table")

    def test_get_primary_keys(self):
        result = self.db_tool.get_primary_keys()
        self.assertIsNotNone(result, "Get primary keys failed.")

    def test_get_row_count(self):
        result = self.db_tool.get_row_count()
        self.assertIsNotNone(result, "Get row count failed.")

    def test_get_id_primary_key_only(self):
        primary_key = "7592f4b7-7d16-4009-b09f-2c1ad220423f"
        primary_key_2 = "test_key"
        expected_sql = "SELECT id FROM test_table WHERE primary_key = 'test_key';"
        self.db_tool.execute_mysql = MagicMock(return_value=2)

        result = self.db_tool.get_id(primary_key_2)

        self.assertEqual(result, 2)
        self.db_tool.execute_mysql.assert_called_once_with(expected_sql)

    def test_get_id_primary_key_and_element_value(self):
        primary_key = "height"
        element_value = "480"
        expected_sql = "SELECT id FROM test_table WHERE height = '480';"
        self.db_tool.execute_mysql = MagicMock(return_value=1)

        result = self.db_tool.get_id(primary_key, element_value)

        self.assertEqual(result, 1)
        self.db_tool.execute_mysql.assert_called_once_with(expected_sql)

    def test_csv2dbtool(self):
        self.db_tool.delete_table(table_name="test_table")
        result = self.db_tool.csv2dbtool()
        value = result.iloc[0][1]
        self.assertEqual(value, "Tomato")
        print("*** done test_csv2dbtool")

if __name__ == "__main__":
    unittest.main()
