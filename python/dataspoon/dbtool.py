import argparse
import csv
import html
import json
import os
from urllib.parse import quote, unquote

import mysql
import pandas
from dotenv import load_dotenv
from mysql.connector import Error

DEFAULT_DATABASE = "default_database"
DEFAULT_TABLE = "default_table"
DEFAULT_INI_FILE_PATH = ''
# key = 'key'
HTML_ESCAPE_TABLE = {
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    " ": "&nbsp",
    "\n": "&#013",
    "True": "_1",
    "False": "_0"
}
HTML_UNESCAPE_TABLE = {
    "&#x27;": "'",
    "&quot;": "\""
}
DEFAULT_PKL_INPUT = '../assets/users.pkl'
DEFAULT_PKL_OUTPUT = '../assets/output.pkl'
MYSQL_DROP_COLUMN = "ALTER TABLE {0} DROP COLUMN {1};"
MYSQL_DELETE_STATEMENT = "DELETE FROM {0} WHERE {1} = '{2}';"
MYSQL_DROP_DATABASE = "DROP DATABASE {0};"
MYSQL_DROP_TABLE = "DROP TABLE {0};"
MYSQL_SELECT_FROM = "SELECT {0} FROM {1};"
# MYSQL_SELECT_SINGLE_ROW_STATEMENT = "SELECT FROM {1} WHERE {2} = '{3}';"
MYSQL_SELECT_ROW_FROM_WHERE = "SELECT {0} FROM {1} WHERE {2} = '{3}';"
ONEHOT_KEY = 'sentence'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATE_STATEMENT = "UPDATE {0} SET {1} = '{2}' WHERE {3} = '{4}';"
COLORS = [
    "red", "blue", "green", "yellow", "purple", "orange",
    "pink", "brown", "gray", "black", "white", "lime",
    "cyan", "magenta", "maroon", "navy", "olive", "teal"
]


class DBTool:
    def __init__(self, database_name=DEFAULT_DATABASE,
                 table_name=DEFAULT_TABLE, user="default", passwd="default", host="default", port="default",
                 onehotdb_name="onehot_database", onehotdb_table="onehot_table"):
        """
         Initializes the DBTool object for handling interactions with the database.

        :param user: User name for the database connection. Defaults to value in .env file.
        :param passwd: Password for the database connection. Defaults to value in .env file.
        :param host: Host address for the database connection. Defaults to value in .env file.
        :param port: Port number for the database connection. Defaults to value in .env file.
        :param database_name: The name of the primary database. Defaults to "svgobject_database".
        :param table_name: The name of the primary table within the database. Defaults to "svgobject_table".
        :param onehotdb_name: The name of the one-hot encoding database. Defaults to "onehot_database".
        :param onehotdb_table: The name of the one-hot encoding table. Defaults to "onehot_table".

        Example Usage:

        # Using default values:
        dbtool = DBTool()

        # Specifying a custom database name:
        xyzzydb = DBTool(database_name='xyzzydb')

        # Specifying both custom database and table name:
        xyzzydb = DBTool(database_name='xyzzydb', table_name='magic_table')

        # Full customization including user, password, host, and port:
        xyzzydb = DBTool(user='bilbo', passwd='baggins', host='127.0.0.1', port='3306', database_name='xyzzydb', table_name='magic_table')

        """

        load_dotenv()
        self.user = os.getenv('DBTOOL_USER') if user == "default" else user
        self.passwd = os.getenv('DBTOOL_PASSWD') if passwd == "default" else passwd
        self.host = os.getenv('DBTOOL_HOST') if host == "default" else host
        self.port = int(os.getenv('DBTOOL_PORT') if port == "default" else port)
        self.database_name = os.getenv(
            'DBTOOL_DATABASE_NAME') if database_name == "svgobject_database" else database_name
        self.table_name = os.getenv('DBTOOL_TABLE_NAME') if table_name == "svgobject_table" else table_name
        self.onehotdb_name = os.getenv('DBTOOL_ONEHOTDB_NAME') if onehotdb_name == "onehot_database" else onehotdb_name
        self.onehotdb_table = os.getenv('DBTOOL_ONEHOTDB_TABLE') if onehotdb_table == "onehot_table" else onehotdb_table
        self.open_database(self.database_name, self.table_name)
        self.write_default_json()
        self.write_advanced_json()
        self.write_default_csv()

    def add_column(self, _column_name):
        """
        DBTool._add_column() adds a column your MySQL database table
        :param _column_name: name of the new column
        """
        query = "ALTER TABLE {0} ADD {1} VARCHAR(256);".format(self.table_name,
                                                               self.get_clean_key_string(_column_name))
        self.execute_mysql(query)

    @staticmethod
    def _get_html_unescape(_string):
        clean_string = str(_string)
        unescape_string = html.unescape(clean_string)
        for item in HTML_UNESCAPE_TABLE:
            unescape_string = unescape_string.replace(item, HTML_UNESCAPE_TABLE.get(item))
        print("_get_html_unescape: " + unescape_string)
        return unescape_string

    def drop_column(self, column_name="None"):
        mysql_drop_column = MYSQL_DROP_COLUMN.format(self.table_name, column_name)
        self.execute_mysql(mysql_drop_column)

    def add_dataframe(self, _data_frame, _primary_key_column_num=0):
        """
        This method adds a dataframe to MySQL
        :param _data_frame: the pandas.DataFrame to be added to self.table_name
        :param _primary_key_column_num: when adding a dataframe each row requires a key.  _primary_key_column_row is the column_number of _data_frame to be used as key then adding each row
        """
        h, w = _data_frame.shape
        for row in range(0, h, 1):
            for column in range(0, w, 1):
                primary_key = _data_frame.iloc[row][_primary_key_column_num]
                column_name = _data_frame.columns[column]
                value = str(_data_frame.iloc[row][column])
                self.put(primary_key, column_name, value)

        print("done add_dataframe")

    @staticmethod
    def convert_value(value):
        if value is None:
            return "None"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            return unquote(str(value))
        return value

    def convert_ints_and_none_to_strings(self, input_list):
        # If input_list is not a list, simply convert the value and return
        if not isinstance(input_list, list):
            return self.convert_value(input_list)

        # Determine if it is a list of lists
        is_nested_list = all(isinstance(item, list) for item in input_list)
        print("list of lists" if is_nested_list else "not list of lists")

        # Convert the elements in the list or nested list
        if is_nested_list:
            converted_list = [[self.convert_value(item) for item in row] for row in input_list]
        else:
            converted_list = [self.convert_value(item) for item in input_list]

        return converted_list

    def csv2dbtool(self, csv_path="default.csv"):
        dataframe = pandas.read_csv(filepath_or_buffer=csv_path, header=0)
        self.add_dataframe(dataframe, 0)
        return self.get_dataframe()

    def delete_database(self, database_name=DEFAULT_DATABASE):
        mysql_drop_database = MYSQL_DROP_DATABASE.format(self.get_clean_key_string(database_name))
        self.execute_mysql(mysql_drop_database)

    def delete_table(self, table_name=DEFAULT_TABLE):
        mysql_delete_data = "DELETE FROM {0};".format(self.get_clean_key_string(table_name))
        self.execute_mysql(mysql_delete_data)

    def execute_mysql(self, _mysql_statement, _value=None):
        """
        DBTool.execute_mysql() executes MySQL commands, which are called by other methods.
        :param _mysql_statement: a formatted string with a MySQL command.
        :param _value: RESERVED for future use
        :return: returns the result of the MySQL statement or an error message.
        """
        result = 'default'
        connection = self.get_db_connection(host_name=self.host, user_name=self.user, user_password=self.passwd,
                                            port_num=self.port, _db_name=self.database_name)
        if connection is not None:
            try:
                cursor = connection.cursor(buffered=True)
                if _value is None:
                    cursor.execute(_mysql_statement)
                else:
                    cursor.execute(_mysql_statement, _value)
                connection.commit()
                if _mysql_statement.startswith('SELECT'):
                    if "*" not in _mysql_statement:
                        result = cursor.fetchone()
                        if result is not None:
                            result = result[0]
                    else:
                        result = cursor.fetchall()
                        if result is not None:
                            result = [list(x) for x in result]
                            if len(result) == 1:
                                result = result[0]
                cursor.close()
                connection.close()
            except Error as err:
                if err.errno == 1054 or str(err.args[1]).endswith('exists') or str(err.args[1]).__contains__(
                        'Duplicate'):
                    print('non-fatal error in dbtool.execute_mysql: ' + _mysql_statement)
                elif err.errno == 1064:
                    print('mysql syntax error: ' + _mysql_statement)
                else:
                    print(f"Error: '{err}'\n" + _mysql_statement + "\n*****")
                return False
        return result

    def get(self, primary_key, column_name=None):
        """
        Retrieves data from the database.

        :param primary_key: Primary key that uniquely identifies the row.
        :param column_name: Optional, the name of the column from which to retrieve the value.
        :return: If column_name=None, returns the entire row. Otherwise, returns the value in the specified column.

        Example Usage:

        # Retrieve the entire row:
        result = dbtool.get('some_primary_key')

        # Retrieve a specific value:
        result = dbtool.get('some_primary_key', 'column_name'
        """
        if column_name is None:
            # 1 result: key returns the entire row for key
            sql_statement = MYSQL_SELECT_ROW_FROM_WHERE.format('*',
                                                               self.table_name,
                                                               'primary_key',
                                                               self.get_clean_key_string(primary_key))
        else:
            # 2 result: returns the value for key on the key row
            sql_statement = MYSQL_SELECT_ROW_FROM_WHERE.format(self.get_clean_key_string(column_name), self.table_name,
                                                               'primary_key',
                                                               self.get_clean_key_string(primary_key))
        result = self.execute_mysql(sql_statement)
        result = self.convert_ints_and_none_to_strings(result)
        return result

    @staticmethod
    def get_clean_key_string(_string=str):
        """
        DBTool().get_clean_key_string() replaces certain characters with web entity values or escape codes.

        :param _string: a string value
        :return: returns a value that is suitable for being used as a name in MySQL

        MySQL has rules about what values can be in an identifier. This method processes string values to comply with the rules.

        clean_value = DBTool().get_clean_key_string("That's great!")

        clean_value = 'That&apos;s&nbspa&nbspgreat!'
        """
        _string = str(_string)
        _string = html.escape(_string)
        return _string

    def get_columns(self, exclude_2_keys=False):
        connection = self.get_db_connection(host_name=self.host, user_name=self.user, user_password=self.passwd,
                                            port_num=self.port, _db_name=self.database_name)
        if connection is not None:
            cursor = connection.cursor(buffered=True)

            # Check if the table exists before executing the query
            check_table_existence_statement = "SHOW TABLES LIKE '{0}';".format(self.table_name)
            cursor.execute(check_table_existence_statement)
            table_exists = cursor.fetchone()

            if table_exists:
                mysql_statement = "SELECT {0} FROM {1};".format('*', self.table_name)
                cursor.execute(mysql_statement)
                columns = list(cursor.column_names)
                if exclude_2_keys:
                    columns.pop(0)
                    columns.pop(0)
                cursor.close()
                connection.close()
                return columns
            else:
                cursor.close()
                connection.close()
                return None
        else:
            return None

    def get_dataframe(self):
        get_all_rows_mysql_statement = MYSQL_SELECT_FROM.format('*', self.table_name)
        all_rows = self.execute_mysql(get_all_rows_mysql_statement)
        # all_rows = self.remove_none(all_rows)
        if all_rows == "default" or all_rows == "None":
            all_rows = self.get_default_all_rows()
        all_rows = self.convert_ints_and_none_to_strings(all_rows)
        columns = self.get_columns(exclude_2_keys=False)

        if len(all_rows) == 0:
            data = {"Column" + str(i + 1): ["default"] for i in range(len(columns))}
            dataframe = pandas.DataFrame(data)
        else:
            dataframe = pandas.DataFrame(all_rows)
            if dataframe.shape[1] == 1:
                dataframe = dataframe.transpose()
        dataframe.columns = columns
        return dataframe

    def get_db_connection(self, host_name="127.0.0.1", user_name="default", user_password="default", port_num=3306,
                          _db_name=DEFAULT_DATABASE):
        connection = None
        try:
            if _db_name is not None:
                connection = mysql.connector.connect(
                    host=host_name,
                    user=user_name,
                    passwd=user_password,
                    port=port_num,
                    database=_db_name
                )
            else:
                connection = mysql.connector.connect(
                    host=host_name,
                    user=user_name,
                    passwd=user_password,
                    port=port_num,
                    database=self.database_name
                )
            # print("python._get_db_connection successful: " + db_name)
        except Error as err:
            # err.errno(1049) is database not exists
            if err.errno == 1049:
                connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    passwd=self.passwd,
                    port=self.port,
                    database='sys'
                )
                try:
                    cursor = connection.cursor(buffered=True)
                    mysql_create_database = "CREATE DATABASE {0};".format(self.get_clean_key_string(_db_name))
                    cursor.execute(mysql_create_database)
                    cursor.close()
                    connection.commit()
                except Error as err:
                    print(f"Error: '{err}'")
            else:
                print('*** DBTool Did you update default.ini: ' + self.user)
                print(f"Error: '{err}'")

                # print('created new database: ' + db_name)
        return connection

    def get_id(self, primary_key, element_value=None):
        """
        DBTool.get_id() returns a row number for either a primary key or a combination of a primary key and key/value pair.
        :param primary_key: The primary key whose corresponding row number is to be retrieved.
        :param element_value: Optional value corresponding to the element_key.
                              Used in conjunction with element_key to refine the search.
        :return: The row ID corresponding to the specified primary key, and possibly the element key/value pair.
        """

        if element_value is None:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name, 'primary_key',
                                                                         self.get_clean_key_string(primary_key))
        else:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name,
                                                                         self.get_clean_key_string(
                                                                             primary_key),
                                                                         self.get_clean_key_string(
                                                                             element_value))

        row_id = self.execute_mysql(select_sql)
        return row_id

    def get_primary_keys(self):
        dataframe = self.get_dataframe()
        primary_keys = dataframe['primary_key'].values.tolist()
        return primary_keys

    def get_row_count(self):
        """
        Sometimes you need to know how many rows are in the table.
        :return: Returns the number of rows in self.table_name.
        """
        get_row_count_mysql = "SELECT COUNT(*) FROM {0};".format(self.table_name)
        row_count = self.execute_mysql(get_row_count_mysql)
        # print('get_row_count: ' + str(row_count[0]))
        return row_count[0]

    def get_values(self, _primary_key, _exclude_2=False):
        values = list(self.get(_primary_key))
        if _exclude_2:
            values.pop(0)
            values.pop(0)
        return values

    def json2dbtool(self, primary_key_name="primary_key",
                    json_file_path="default.json"):
        """
        Inserts the contents of a JSON file into a database using the DBTool class's put method.

        :param primary_key_name: The name of the key in the JSON data that will be used as the primary key for the database. Default is "primary_key".
        :param json_file_path: The path to the JSON file that contains the data to be inserted. Defaults to the given path.

        Example JSON structure:
        {
            "primary_key": "3c401888-b6b0-4806-aafc-c8888a4899af",
            "directory": "imagine/",
            "file_identifier": "puppy",
            ...
        }

        :return: The ID of the affected row, retrieved using the `get_id` method and the primary key.
        """
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        primary_key = data[primary_key_name]

        # Insert or update primary_key
        self.put(primary_key=primary_key)

        # Loop through other keys in the JSON object and use the put method to update the values in the DB
        for element_key, value in data.items():
            if element_key != primary_key_name:  # Avoid reinserting the primary key
                self.put(primary_key=primary_key, element_key=element_key, value=value)

        return self.get_dataframe()

    def open_database(self, _database_name, _table_name=None):
        """
        Opens a database and optionally a table in the MySQL server.

        This method establishes a connection to the specified database and, if provided, a table within that database.

        :param _database_name: The name of the database to open.
        :param _table_name: Optional. The name of the table to open within the database.

        Note:
        - The `self.table_name` attribute remains unchanged when using `open_database`.
        - The `self.table_name` attribute is used in various methods such as `_add_column`, `get`, `get_id`, `open_table`, `_add_dataframe`, and `put`.
        - The default value for `self.table_name` is set in the `.env` file.

        After successfully opening the database and table, a MySQL query is executed to create the specified database,
        and the `open_table` method is called to initialize the selected table.
        """
        self.database_name = self.get_clean_key_string(_database_name)
        if _table_name is not None:
            self.table_name = self.get_clean_key_string(_table_name)

        open_database_mysql = "CREATE DATABASE {0};".format(self.database_name)
        self.execute_mysql(open_database_mysql)
        self.open_table(self.table_name)

        print('open_database: ' + self.database_name)

    def open_table(self, _table_name):
        self.table_name = self.get_clean_key_string(_table_name)
        mysql_open_table = "CREATE TABLE {0} ({1} int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,  {2} varchar(256));".format(
            self.table_name, 'id', 'primary_key')
        self.execute_mysql(mysql_open_table)

    def put(self, primary_key="xyzzy_primary_key", element_key=None, value=None):
        """
        Inserts or updates data in the database.

        :param primary_key: Primary key identifying the row of data.
        :param element_key: Key for the value to be updated in the row.
        :param value: Value to be associated with the provided element_key.
        :return: Row number of the affected row.

        Example Usage:

        # Insert or update a specific value:
        row_num = dbtool.put('some_primary_key', 'element_key', 'value')
        """
        primary_key_id = self.get_id(primary_key)
        if primary_key_id == 0 or primary_key_id is None or primary_key_id == "None":
            mysql_statement = "INSERT INTO {0} ({1}) VALUES ('{2}');".format(
                self.table_name, 'primary_key', self.get_clean_key_string(primary_key))
            self.execute_mysql(mysql_statement)
            primary_key_id = self.get_id(primary_key)

        if element_key is not None and value is not None:
            self.add_column(element_key)
            if isinstance(value, int):
                value = str(value)
            value = value.replace("#", "&#35;")
            value_escaped = self.escape_nonascii(value)

            mysql_statement = "UPDATE {0} SET {1} = '{2}' WHERE {3} = '{4}';".format(
                self.table_name, element_key, value_escaped, 'primary_key', self.get_clean_key_string(primary_key))
            self.execute_mysql(mysql_statement)

        return primary_key_id

    @staticmethod
    def escape_nonascii(input_dict):
        escaped_dict = {}
        try:
            for key, value in input_dict.items():
                if isinstance(value, str):
                    escaped_value = quote(value, safe='')
                else:
                    escaped_value = value
                escaped_dict[key] = escaped_value
            return escaped_dict
        except:
            escaped_value = quote(input_dict, safe='')
            return escaped_value

    @staticmethod
    def unescape_nonascii(input_data):
        try:
            if isinstance(input_data, dict):
                unescaped_dict = {key: unquote(value) if isinstance(value, str) else value for key, value in
                                  input_data.items()}
                return unescaped_dict
            elif isinstance(input_data, list):
                unescaped_list = []
                for row in range(len(input_data)):
                    this_row = input_data[row]
                    this_unescaped_list = [unquote(item) if isinstance(item, str) else item for item in this_row]
                    unescaped_list.append(this_unescaped_list)
                return unescaped_list
            else:
                return unquote(input_data)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return input_data

    @staticmethod
    def remove_none(_result):
        if _result is None:
            _result = 'None'
        if type(_result) == list:
            if len(_result) == 1:
                for column_index in range(len(_result)):
                    temp_value = _result[column_index]
                    if temp_value is None:
                        _result[column_index] = 'None'
        else:
            for index in range(len(_result)):
                temp_row = _result[index]
                for column_index in range(len(temp_row)):
                    temp_value = _result[index][column_index]
                    if temp_value is None:
                        _result[index][column_index] = 'None'
        return _result

    def to_pickle(self, _file_path):
        dataframe = self.get_dataframe()
        dataframe.to_pickle(_file_path)
        print('pickle_words: ' + _file_path)

    def get_column(self, column_name):
        dataframe = self.get_dataframe()
        column_values = dataframe[column_name].values.tolist()
        print('get_column done!')
        return column_values

    def write_default_json(self):
        data = {
            "database_name": self.database_name,
            "table_name": self.table_name,
            "directory": "imagine/",
            "file_identifier": "puppy",
            "height": 480,
            "width": 480,
            "inference_steps": 20,
            "seed": "78901427222289238",
            "primary_key": "7592f4b7-7d16-4009-b09f-2c1ad220423f",
            "file_type": "png"
        }

        with open('default.json', 'w') as file:
            json.dump(data, file, indent=4)

    def write_advanced_json(self):
        data = {
            "database_name": self.database_name,
            "table_name": self.table_name,
            "characters": [
                {
                    "name": "Harry Potter",
                    "house": "Gryffindor",
                    "wand": "11\", Holly, phoenix feather core",
                    "patronus": "Stag"
                },
                {
                    "name": "Hermione Granger",
                    "house": "Gryffindor",
                    "wand": "10¾\", Vine wood, dragon heartstring core",
                    "patronus": "Otter"
                },
                {
                    "name": "Severus Snape",
                    "house": "Slytherin",
                    "wand": "Unknown",
                    "patronus": "Doe"
                }
            ],
            "houses": [
                "Gryffindor",
                "Hufflepuff",
                "Ravenclaw",
                "Slytherin"
            ],
            "spells": [
                {
                    "name": "Expelliarmus",
                    "type": "Charm",
                    "effect": "Disarms opponent"
                },
                {
                    "name": "Wingardium Leviosa",
                    "type": "Charm",
                    "effect": "Makes objects float"
                },
                {
                    "name": "Alohomora",
                    "type": "Charm",
                    "effect": "Opens locked doors"
                }
            ],
            "quidditch_teams": [
                "Gryffindor Quidditch Team",
                "Hufflepuff Quidditch Team",
                "Ravenclaw Quidditch Team",
                "Slytherin Quidditch Team"
            ]
        }

        with open('advanced.json', 'w') as file:
            json.dump(data, file, indent=4)

    def write_default_csv(self):
        # Define a list of vegetables with their common names and scientific names
        vegetables = [
            ['Common Name', 'Scientific Name'],
            ['Tomato', 'Solanum lycopersicum'],
            ['Carrot', 'Daucus carota'],
            ['Potato', 'Solanum tuberosum'],
            ['Cabbage', 'Brassica oleracea'],
            ['Spinach', 'Spinacia oleracea'],
            ['Onion', 'Allium cepa'],
            ['Broccoli', 'Brassica oleracea var. italica'],
            ['Cucumber', 'Cucumis sativus']
        ]

        # Open the CSV file for writing
        with open('default.csv', 'w+', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write the rows to the CSV file
            writer.writerows(vegetables)

        print('CSV file written successfully.')


class OneHotWords(DBTool):
    # mysql has a maximum number of 4096 columns per table
    # Therefore, each sentence has a maximum number of words
    def __init__(self, onehotdb_name=None, onehotdb_table=None, config_key=None):
        load_dotenv()
        onehotdb_name = onehotdb_name if onehotdb_name else os.getenv('DBTOOL_ONEHOTDB_NAME')
        onehotdb_table = onehotdb_table if onehotdb_table else os.getenv('DBTOOL_ONEHOTDB_TABLE')

        super().__init__(onehotdb_name, onehotdb_table)
        # print('__init__ done!')

    def get_word(self, _index):
        # try to get the word at _index, if it fails then add _index
        result = self.get(primary_key=_index, column_name='primary_key')
        if result is None:
            result = 'default'
        return html.unescape(str(result))

    def get_index(self, _word):
        # This function returns the row number of _word in the onehot index
        clean_word = self.get_clean_key_string(_word)
        row_number = self.get(primary_key=clean_word, column_name='id')
        return row_number

    def get_words(self):
        words = self.get_column(column_name='key')
        print('get_words done!')
        return words


DEFAULT_INI = {
    "user": "bilbo",
    "passwd": "baggins",
    "port": "3306",
    "host": "127.0.0.1",
    "database_name": "dbtool_db",
    "table_name": "dbtool_table",
    "onehotdb_name": "onehotwords",
    "onehotdb_table": "words",
    "words_filename_key": "default_words"
}


def main():
    parser = argparse.ArgumentParser(description="Command-line interface for DBTool")
    parser.add_argument("--get", metavar="PRIMARY_KEY", help="Retrieve data using primary key")
    parser.add_argument("--column", metavar="COLUMN_NAME", help="Optional, specify a column for --get")
    parser.add_argument("--put", metavar="PRIMARY_KEY", help="Insert or update data using primary key")
    parser.add_argument("--element", metavar="ELEMENT_KEY", help="Key for the value to be updated with --put")
    parser.add_argument("--value", metavar="VALUE", help="Value to be updated with --put")
    parser.add_argument("--json2db", metavar="JSON_FILE_PATH", help="Path to JSON file for database insertion")
    parser.add_argument("--primary_key_name", metavar="PRIMARY_KEY_NAME", help="Primary key name for JSON to DB",
                        default="primary_key")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()  # Print help message when no arguments are provided
        exit()

    dbtool = DBTool()

    if args.get:
        result = dbtool.get(args.get, args.column)
        print(result)

    if args.put and args.element and args.value:
        row_num = dbtool.put(args.put, args.element, args.value)
        print(f"Updated row number: {row_num}")

    if args.json2db:
        row_id = dbtool.json2dbtool(primary_key_name=args.primary_key_name, json_file_path=args.json2db)
        print(f"Updated row with ID: {row_id}")

    print("dbtool.main() done!")

if __name__ == '__main__':
    main()
    print("dbtool done!")