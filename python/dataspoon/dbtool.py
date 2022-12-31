import html
import os

import mysql
import pandas
from mysql.connector import Error

from python.dataspoon.configtool import ConfigTool

LINK_KEY = 'link_key'
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
MYSQL_SELECT_ROW_STATEMENT = "SELECT {0} FROM {1} WHERE {2} = '{3}';"
MYSQL_SELECT_SINGLE_ROW_STATEMENT = "SELECT FROM {1} WHERE {2} = '{3}';"
UPDATE_STATEMENT = "UPDATE {0} SET {1} = '{2}' WHERE {3} = '{4}';"
MYSQL_DELETE_STATEMENT = "DELETE FROM {0} WHERE {1} = '{2}';"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ONEHOT_KEY = 'sentence'
DEFAULT_PKL_INPUT = '../../data/users.pkl'
DEFAULT_PKL_OUTPUT = '../../data/output.pkl'


class DBTool:
    def __init__(self, _database_name=None, _table_name=None, _config_key=None):
        """
        DBTool() provides access to MySQL functions within Python.

        :param _database_name: Optionally, specify self.database_name
        :param _table_name: Optionally, specify self.table_name
        :param _config_key: Optionally, specify ConfigTool(_config_key); default is 'bilbo'
        To open the default database:

        dbtool = DBTool()

        To open a database named 'xyzzydb'

        xyzzydb = DBTool('xyzzydb')

        To open a database named 'xyzzydb' and a table named 'magic_table'

        xyzzydb = DBTool('xyzzydb', 'magic_table')

        """
        self.base_dir = ROOT_DIR.rsplit('/', 0)[0] + '/'
        try:
            open('../../default.ini', 'r+')
        except FileNotFoundError:
            config_tool = ConfigTool('default')
            config_tool.write_default_configs()
        configtool = ConfigTool('default' if _config_key is None else _config_key)
        these_configs = configtool.get_configs()
        self.user = these_configs.get('user')
        self.passwd = these_configs.get('passwd')
        self.host = these_configs.get('host')
        self.port = these_configs.get('port')
        self.database_name = (these_configs.get('database_name') if _database_name is None else _database_name)
        self.table_name = (these_configs.get('table_name)') if _table_name is None else _table_name)
        self.onehotdb_name = these_configs.get('onehotdb_name')
        self.onehotdb_table = these_configs.get('onehotdb_table')
        self.open_database(self.database_name)
        # self.open_table(self.table_name)
        # print('__init__ done!')

    def _add_column(self, _column_name):
        """
        DBTool._add_column() adds a column your MySQL database table
        :param _column_name: name of the new column
        """
        query = "ALTER TABLE {0} ADD {1} VARCHAR(4096);".format(self.table_name,
                                                                self.get_clean_key_string(_column_name))
        # values = [self.table_name, self.get_clean_key_string(_column_name)]

        self._execute_mysql(query)
        # print('Add column: '+ _column_name)

    def _get_db_connection(self, host_name, user_name, user_password, port_num, _db_name=None):
        connection = None
        try:
            if _db_name is not None:
                connection = mysql.connector.connect(
                    host=host_name,
                    user=user_name,
                    passwd=user_password,
                    port=port_num,
                    database=self.get_clean_key_string(_db_name)
                )
                self.database_name = self.get_clean_key_string(_db_name)
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
                    self.database_name = self.get_clean_key_string(_db_name)
                    # print("_get_db_connection created database: " + db_name)
                except Error as err:
                    print(f"Error: '{err}'")
            else:
                print('_get_db_connection error: ' + _db_name)
                # print('created new database: ' + db_name)
        return connection

    @staticmethod
    def _get_html_escape(_string):
        # clean_string = str(_string)
        # print("***** test: " + clean_string)
        # clean_string = "".join(HTML_ESCAPE_TABLE.get(c, c) for c in str(_string))
        clean_string = html.escape(_string)
        print('get_html_escape: ' + clean_string)
        return clean_string

    @staticmethod
    def _get_html_unescape(_string):
        clean_string = str(_string)
        clean_string = clean_string.lstrip('_')
        unescape_string = html.unescape(clean_string)
        for item in HTML_UNESCAPE_TABLE:
            unescape_string = unescape_string.replace(item, HTML_UNESCAPE_TABLE.get(item))
        print("_get_html_unescape: " + unescape_string)
        return unescape_string

    def _execute_mysql(self, _mysql_statement, _value=None):
        """
        DBTool._execute_mysql() executes MySQL commands, which are called by other methods.
        :param _mysql_statement: a formatted string with a MySQL command.
        :param _value: RESERVED for future use
        :return: returns the result of the MySQL statement or an error message.
        """
        result = 'default'
        try:
            connection = self._get_db_connection(self.host, self.user, self.passwd, self.port, self.database_name)
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
            if err.errno == 1054 or str(err.args[1]).endswith('exists') or str(err.args[1]).__contains__('Duplicate'):
                print('non-fatal error in dbtool._execute_mysql: ' + _mysql_statement)
            elif err.errno == 1064:
                return 'mysql syntax error: ' + _mysql_statement
            else:
                print(f"Error: '{err}'\n" + _mysql_statement + "\n*****")
            return False
        return result

    @staticmethod
    def _replace_none(_lists):
        if type(_lists) == list and len(_lists) > 0:
            if type(_lists[0]) == list:
                for list_index in range(0, len(_lists)):
                    _lists[list_index] = ['None' if v is None else v for v in _lists[list_index]]
                    print('replace many')
            else:
                _lists = ['None' if v is None else v for v in _lists]
        _lists = ['default']
        return _lists

    def add_dataframe(self, _data_frame, _link_key_column_num=0):
        """

        :param _data_frame: the pandas.DataFrame to be added to self.table_name
        :param _link_key_column_num: when adding a dataframe each row requires a link_key.  _link_key_column_row is the column_number of _data_frame to be used as link_key then adding each row
        """

        h, w = _data_frame.shape
        for row in range(0, h, 1):
            link_key = str(_data_frame.iloc[row][_link_key_column_num])
            for column in range(0, w, 1):
                key = str(_data_frame.columns[column])
                value = str(_data_frame.iloc[row][column])
                self.put(link_key, key, value)
        # print('_add_dataframe done!')

    def copy_link_key(self, _from_link_key, _to_link_key):
        # this method creates a shallow paste by ignoring None values in _from_link_key
        # if a key/value is null then skip (or consider set value as 'default' for deep paste)
        # index 0 is id and index 1 is link_key, copied values thus begin at index 2
        # if the _from_link_key does not exist then create it
        # if the _to_link_key does not exist then create it
        if self.get_id(_from_link_key) == 0:
            self.put(_from_link_key)
        else:
            old_values = self.get_values(_from_link_key)
            old_keys = self.get_columns()
            # if the _to_link_key does not exist then create it
            if self.get_id(_to_link_key) == 0:
                self.put(_to_link_key)
            # index 0 is id and index 1 is link_key, copied values thus begin at index 2
            for index in range(2, len(old_keys), 1):
                if old_values[index] is None:
                    # if a key/value is null then consider setting value s 'default'
                    # self.put(_to_link_key, old_keys[index], 'default')
                    pass
                else:
                    # otherwise, insert the old_value
                    self.put(_to_link_key, old_keys[index], old_values[index])
        return self.get_id(_to_link_key)

    def delete_database(self, _database_name):
        mysql_drop_database = "DROP DATABASE {0}".format(self.get_clean_key_string(_database_name))
        self._execute_mysql(mysql_drop_database)
        # print('delete_database: ' + _database_name)

    def delete_table(self, _table_name):
        mysql_drop_table = "DROP TABLE {0}".format(self.get_clean_key_string(_table_name))
        self._execute_mysql(mysql_drop_table)  # print('delete_table: ' + _table_name)

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
        if _string.isdigit():
            _string = "_" + str(_string)
        # _string = "".join(HTML_ESCAPE_TABLE.get(c, c) for c in str(_string))
        _string = html.escape(_string)
        return _string

    def get_columns(self, _exclude_2_keys=False):
        connection = self._get_db_connection(self.host, self.user, self.passwd, self.port, self.database_name)
        cursor = connection.cursor(buffered=True)
        mysql_statement = "SELECT {0} FROM {1};".format('*', self.table_name)
        cursor.execute(mysql_statement)
        columns = list(cursor.column_names)
        if _exclude_2_keys:
            columns.pop(0)
            columns.pop(0)
        cursor.close()
        connection.close()
        return columns

    def get_dataframe(self):
        get_all_rows_mysql_statement = "SELECT * FROM {0}".format(self.table_name)
        all_rows = self._execute_mysql(get_all_rows_mysql_statement)
        dataframe = pandas.DataFrame(all_rows)
        columns = self.get_columns(_exclude_2_keys=False)
        dataframe.columns = columns
        return dataframe

    def get_id(self, _link_key, _value=None):
        """
        DBTool.get_id() returns a row number for either a link_key or key/value pair.
        :param _link_key: _link_key uniquely identifies the row.
        :param _value: _key is an optional parameter, which is used to identify the column name.
        :return: If _key=None then return the row_number where link_key = _link_key.  Otherwise, return the ro_number where a key/value pair matches _link_key/_key_value.
        """

        if _value is None:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name, LINK_KEY,
                                                                         self.get_clean_key_string(_link_key))
        else:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name,
                                                                         self.get_clean_key_string(_link_key),
                                                                         self.get_clean_key_string(_value))

        link_key_id = self._execute_mysql(select_sql)
        if link_key_id is None:
            print('get_id: ' + str(link_key_id))
            return 0
        else:
            print('get_id: ' + str(link_key_id))
            return link_key_id

    def get_link_keys(self):
        dataframe = self.get_dataframe()
        link_keys = dataframe[LINK_KEY].values.tolist()
        # link_key_array = link_keys.
        print('get_sentence_indices done!')
        return link_keys

    def get_row_count(self):
        """
        Sometimes you need to know how many rows are in the table.
        :return: Returns the number of rows in self.table_name.
        """
        get_row_count_mysql = "SELECT COUNT(*) FROM {0};".format(self.table_name)
        row_count = self._execute_mysql(get_row_count_mysql)
        # print('get_row_count: ' + str(row_count[0]))
        return row_count[0]

    def get_values(self, _link_key, _exclude_2=False):
        values = list(self.get(_link_key))
        if _exclude_2:
            values.pop(0)
            values.pop(0)
        return values

    def get(self, _link_key=str, _key=None):
        """
        DBTool.get() returns an entire row or the value of a column within a row.
        :param _link_key: _link_key uniquely identifies the row.
        :param _key: _key is an optional parameter, which is used to identify the column name.
        :return: If _key=None then return the entire row.  Otherwise, return the value in the column named _key.
        """
        if _key is None:
            # 1 result: link_key returns the entire row for link_key
            self._add_column(LINK_KEY)
            sql_statement = MYSQL_SELECT_ROW_STATEMENT.format('*',
                                                              self.table_name,
                                                              LINK_KEY,
                                                              self.get_clean_key_string(_link_key))
        else:
            # 2 result: returns the value for key on the link_key row
            self._add_column(_link_key)
            sql_statement = MYSQL_SELECT_ROW_STATEMENT.format(self.get_clean_key_string(_key), self.table_name,
                                                              LINK_KEY,
                                                              self.get_clean_key_string(_link_key))
        result = self._execute_mysql(sql_statement)
        return self.remove_none(result)

    def open_database(self, _database_name, _table_name=None):
        # self.database_name = str(re.sub(LEGAL_CHARACTERS, '_', _database_name.strip()))
        self.database_name = self.get_clean_key_string(_database_name)
        if _table_name is not None:
            # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
            self.table_name = self.get_clean_key_string(_table_name)

        # When you open_database self.table_name does not change
        # self.table is used in: _add_column, get, get_id, open_table, _add_dataframe, and put
        # The default value for self.table_name is python
        # Therefore, _table_name may be required for open_database

        # self.database_name = _database_name
        # open_table_mysql = "CREATE TABLE " + self.table_name + "(id int(10) NOT NULL AUTO_INCREMENT," + LINK_KEY + " varchar(255), PRIMARY KEY (id))"
        open_database_mysql = "CREATE DATABASE {0};".format(self.get_clean_key_string(_database_name))
        self._execute_mysql(open_database_mysql)
        self.open_table(self.table_name)
        print('open_database: ' + _database_name)

    def open_table(self, _table_name):
        # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
        self.table_name = self.get_clean_key_string(_table_name)
        # clean_table_name = self.get_clean_key_string(self.table_name)
        mysql_open_table = "CREATE TABLE {0} ({1} int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,  {2} varchar(4096));".format(
            self.table_name, 'id', LINK_KEY)
        self._execute_mysql(mysql_open_table)
        # self._add_column('link_key')
        # print('open_table: ' + _table_name)

    def put(self, _link_key, _key_value=None, _value=None):
        """
        DBTool().put() inserts values and returns the id of the affected record.

        DBTool().put() behaves differently depending upon the number of parameters that are passed:
            1) adds a row with link_key = _link_key
            2) copies the key/value pairs from _link_key to _link_key_value
            3) sets a key/value pair in _link_key

        :param _link_key: the value used to identify the row of data
        :param _key_value: if 2 parameters then is the row for the key/value pairs in _link_key; if 3 parameters then is the key for _value
        :param _value: is the value for key named _link_key_value in row _link_key
        :return: returns the row_number of the affected row
        """
        # returns row_number of _link_key
        # 1 value: new_link_key
        # 2 value: old_link_key_value, new_link_key_value
        # 3 value: link_key, key, value
        if _key_value is None:
            link_key_id = self.get_id(_link_key)
            if link_key_id == 0:
                mysql_statement = "INSERT INTO {0} ({1}) VALUES ('{2}');".format(self.table_name,
                                                                                 LINK_KEY,
                                                                                 self.get_clean_key_string(_link_key))
                self._execute_mysql(mysql_statement)
            link_key_id = self.get_id(_link_key)
        elif _value is None:
            link_key_id = self.copy_link_key(_link_key, _key_value)
        else:
            # sets value in the column _link_key_value to _key_value in the row where the link_key is _link_key
            if self.get_id(_link_key) == 0:
                self.put(_link_key)
            self._add_column(_key_value)
            link_key_id = self.update_value(_link_key, _key_value, html.escape(_value))
        return link_key_id

    @staticmethod
    def remove_none(_result):
        if _result is None:
            _result = 'None'
        if type(_result) == list:
            for index in range(0, len(_result), 1):
                if _result[index] is None:
                    _result[index] = 'None'
        return _result

    def to_pickle(self, _file_path):
        dataframe = self.get_dataframe()
        dataframe.to_pickle(_file_path)
        print('pickle_words: ' + _file_path)

    def update_value(self, _link_key, _key, _value):
        mysql_insert_statement = UPDATE_STATEMENT.format(self.table_name, self.get_clean_key_string(_key),
                                                         self.get_clean_key_string(_value), 'id',
                                                         self.get_id(_link_key))
        self._execute_mysql(mysql_insert_statement)
        return self.get_id(_link_key)

    def get_column(self, _column_name):
        dataframe = self.get_dataframe()
        column_values  = dataframe[_column_name].values.tolist()
        print('get_column done!')
        return column_values


class OneHotWords(DBTool):
    # mysql has a maximum number of 4096 columns per table
    # Therefore, each sentence has a maximum number of words
    def __init__(self, _config_key=None):
        configtool = ConfigTool('default' if _config_key is None else _config_key)

        super().__init__(configtool.get_configs().get('onehotdb_name'), configtool.get_configs().get('onehotdb_table'))
        # print('__init__ done!')

    def get_word(self, _index):
        # try to get the word at _index, if it fails then add _index
        sql_statement = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format(LINK_KEY,
                                                                        self.table_name,
                                                                        'id',
                                                                        str(_index))
        this_word = self._execute_mysql(sql_statement)
        if this_word is None:
            this_word = 'default'
        return html.unescape(this_word)

    def get_index(self, _word):
        # This function returns the row number of _word in the onehot index
        clean_word = self.get_clean_key_string(_word)
        row_number = super().get_id(clean_word)
        return row_number

    def get_words(self):
        words = super().get_column(LINK_KEY)
        print('get_words done!')
        return words


def test_get_row_count():
    dbtool = DBTool()
    row_count = dbtool.get_row_count()
    print('test_get_row_count: ' + str(row_count))


def test_get_clean_key():
    KEY = "Instrument #"
    dbtool = DBTool()
    clean_key = dbtool.get_clean_key_string(KEY)
    print("test_get_clean_key: '" + KEY + "' = '" + clean_key + "'")


def test_add_data_frame():
    # create the test data_frame
    data = [['bilbo', 'thoron'], ['baggins', 'falbright']]
    data_frame = pandas.DataFrame(data)
    data_frame = data_frame.transpose()
    columns = ['username', 'password']
    data_frame.columns = columns
    # test the system
    dbtool = DBTool()
    dbtool.add_dataframe(data_frame)
    print('test_add_dataframe: ')


def create_simple_pkl():
    # create the test data_frame and pickle file
    user_data = [['bilbo', 'thoron'], ['baggins', 'falbright']]
    data_frame = pandas.DataFrame(user_data)
    data_frame = data_frame.transpose()
    columns = ['username', 'password']
    data_frame.columns = columns
    data_frame.to_pickle(DEFAULT_PKL_INPUT)


def test_to_pickle():
    dbtool = DBTool()
    dbtool.to_pickle('../../data/mysql.pkl')
    print('test_to_pickle done!')


def github_demo_1():
    xyzzydb = DBTool()
    xyzzydb = DBTool('xyzzydb')
    xyzzydb = DBTool('xyzzydb', 'new_magic_table')
    xyzzydb.put('link_key_xyzzy')
    xyzzydb.put('link_key_xyzzy', 'revised_link_key_xyzzy')
    xyzzydb.put('revised_link_key_xyzzy', 'ala', 'kazam')
    print('github_demo done!')


def test_get_row_number():
    dbtool = DBTool('dbtool_test_db', 'dbtool_test_table')
    row_number_1 = dbtool.get_id('xyzzy')
    row_number_2 = dbtool.get_id('new_link_key')
    row_number_3 = dbtool.get_id('failures', '543')
    row_number_4 = dbtool.get_id('failures', '123')
    print('test_get_row_number done!')


def test_onehotwords():
    onehotwords = OneHotWords()
    word_index_1 = onehotwords.get_index('the')
    word_index_2 = onehotwords.get_index('qwerty')
    word_value_1 = onehotwords.get_word(12)

    print('test_onehotwords done!')


def test_delete_database():
    temp_dbtool = DBTool('temp_db')
    temp_dbtool.delete_database('temp_db')


def test_delete_table():
    dbtool = DBTool('test_out_word_db', 'put_word_table')
    dbtool.open_table('temp_table')
    dbtool.delete_table('temp_table')
    print('test_delete_table done!')


def test_get_html_unescape():
    dbtool = DBTool('test_out_word_db', 'put_word_table')
    test_unescape = dbtool._get_html_unescape('asdf&quot;erhert&quot;')
    print('test_get_html_unescape: ' + test_unescape)


def test_init():
    dbtool = DBTool()
    # print('test_init done!')


def test_static_operation():
    DBTool().put('1234', '5678', '9101112')
    test_value = DBTool().get('1234', '5678')
    print('test_static_operation test_value: ' + test_value)
    DBTool('magicdb').put('xyzzy', 'ala', 'kazam')
    DBTool().put('xyzzy', 'ala', 'kazam')
    value = DBTool().get('xyzzy', 'ala')
    print('value: ' + value)


def test_put():
    dbtool = DBTool('dbtool_test_db', 'dbtool_test_table')
    row_1 = dbtool.put('link_key_1')
    row_1 = dbtool.put('link_key_1', 'first_key', 'link_key_1_first_value')
    row_1 = dbtool.put('link_key_1', 'second_key', 'link_key_1_second_value')
    row_2 = dbtool.put('link_key_2', 'first_key', 'link_key_2_first_value')
    row_2 = dbtool.put('link_key_1', 'link_key_2')
    row_2 = dbtool.put('link_key_2', 'xyzzy_key', "link_key_2_xyzzy_key")
    row_1 = dbtool.put('link_key_2', "link_key_1")
    row_2 = dbtool.put('link_key_2', 'second_key', "link_key_2_xyzzy")
    row_3 = dbtool.put('link_key_2', 'link_key_3')
    row_3 = dbtool.put('link_key_1', 'link_key_3')
    row_3 = dbtool.put('link_key_3', 'magic_key', "link_key_3_magic_key")
    row_3 = dbtool.put('link_key_2', 'link_key_3')
    row_3 = dbtool.put('link_key_3', 'first_key', 'link_key_3_first_key_xyzzy')
    print('test_put done!')


def test_get():
    dbtool = DBTool('dbtool_test_db', 'dbtool_test_table')
    columns = dbtool.get_columns()
    link_keys = dbtool.get_link_keys()
    rows = []
    for link_key in link_keys:
        this_row = dbtool.get(link_key)
        for column in columns:
            value = dbtool.get(link_key, column)
            print("*** test_get link_key: " + link_key + " \n*** column: " + column + " \n*** value: " + str(value))
        rows.append(this_row)
    print('test_get done!')


if __name__ == '__main__':
    test_put()
    test_get()
    test_onehotwords()
    test_static_operation()
    test_get_html_unescape()
    test_init()
    test_get_row_number()
    test_get_row_count()
    create_simple_pkl()
    test_add_data_frame()
    test_get_clean_key()
    github_demo_1()
    test_to_pickle()
    test_delete_database()
    test_delete_table()

    # the following line is not reached because of sys.exit() in python()
    print("dbtool done!")
