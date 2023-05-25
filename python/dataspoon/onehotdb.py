import html
import os

import mysql
import numpy
import pandas
from mysql.connector import Error

from python.dataspoon.configtool import ConfigTool
from python.dataspoon.dbtool import OneHotWords
from python.dataspoon.textprocessor import TextProcessor

FILE_PATH_CONFIG_INI = '../configuration.ini'
DB_NAME = 'onehotdb'
FORBIDDEN_DATABASES = ['users']
HASH_MOD = 1
# host = 'localhost'
# host = '192.168.1.227'
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
ILLEGAL_WORDS = ['True']
LEGAL_CHARACTERS = r"[^'a-zA-Z0-9\s\·\,\.\:\:\(\)\[\]\\\\]]"
LINK_KEY = 'link_key'
ONEHOT_DB_NAME = 'onehot_tool'
ONE_HOT_WORD_TABLE_NAME = 'test_dict'
PASSWD = 'baggins'
# port = '50011'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)).rsplit('/', 1)[0] + '/'
MYSQL_CREATE_DATABASE = "CREATE DATABASE {0};"
MYSQL_CREATE_TABLE = "CREATE TABLE {0} ({1} int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,  {2} TEXT NOT NULL DEFAULT 'default');"
MYSQL_SELECT_STATEMENT = "SELECT {0} FROM {1} WHERE {2} = '{3}';"
MYSQL_SELECT_ROW_STATEMENT = "SELECT {0} FROM {1} WHERE {2} = '{3}';"
MYSQL_SELECT_SINGLE_ROW_STATEMENT = "SELECT FROM {1} WHERE {2} = '{3}';"
MYSQL_UPDATE_STATEMENT = "UPDATE {0} SET {1} = '{2}' WHERE {3} = '{4}';"
MYSQL_DELETE_STATEMENT = "DELETE FROM {0} WHERE {1} = '{2}';"
MYSQL_DROP_TABLE = "DROP TABLE {0};"
MYSQL_DROP_DATABASE = "DROP DATABASE {0};"
SENTENCE_KEY = 'sentence'
TABLE_NAME = 'sentences'
USER = 'bilbo'


class OneHotDB:

    def __init__(self, _database_name=None, _table_name=None, _config_key=None):
        """
        OneHotDB takes data, breaks it into smaller parts, and then stores indices to those smaller parts in a database.  Those smaller parts are stored using OneHotWords.

        :param _database_name: Optionally, specify a database_name.  The default database_name is onehotdb.
        :param _table_name: Optionally, specify a table_name.  The default table_name is sentences.
        :param _config_key: Optionally, specify a configuration key.  (ex. 'default')  The default configuration key is default, which maps to a file named "default.ini", located in the project root.
        """

        self.base_dir = ROOT_DIR.rsplit('/', 1)[0] + '/'
        # self.database_name = DB_NAME
        # self.table_name = TABLE_NAME
        # self.open_database(self.database_name)
        # self.open_table(self.table_name)

        self.base_dir = ROOT_DIR.rsplit('/', 0)[0] + '/'
        try:
            open('default.ini', 'r+')
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
        self.table_name = (these_configs.get('table_name') if _table_name is None else _table_name)
        self.onehotdb_name = these_configs.get('onehotdb_name')
        self.onehotdb_table = these_configs.get('onehotdb_table')
        self.words_filename_key = these_configs.get('words_filename_key')  # used in pickle_words
        self.open_database(self.database_name)
        # self.open_table(self.table_name)
        # print('__init__ done!')

    def _add_column(self, _column_name):
        """
        DBTool._add_column() adds a column your MySQL database table
        :param _column_name: name of the new column
        """
        query = "ALTER TABLE {0} ADD {1} BLOB;".format(self.table_name,
                                                                self.get_clean_key_string(_column_name))
        # values = [self.table_name, self.get_clean_key_string(_column_name)]

        self._execute_mysql(query)
        # print('Add column: '+ _column_name)

    def _copy_row(self, _from_link_key, _to_link_key):
        """
        _copy_row copies the values from one row to another.

        :param _from_link_key: the link_key for the row that you want to copy
        :param _to_link_key: the link_key for the destination row
        :return: This function returns the 'id' of the destination row.
        """
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

    def _execute_mysql(self, _mysql_statement, _value=None):
        result = 'default'
        try:
            connection = self._get_db_connection(self.host, USER, PASSWD, self.port, self.database_name)
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
                print('non-fatal error in python._execute_mysql: ' + _mysql_statement)
            elif err.errno == 1064:
                return 'mysql syntax error: ' + _mysql_statement
            else:
                print(f"Error: '{err}'\n" + _mysql_statement + "\n*****")
            return False
        return result

    def _get_column_names(self):
        """
        :return: This function returns the names of the columns for the currently active table.
        """
        connection = self._get_db_connection(self.host, USER, PASSWD, self.port, self.database_name)
        cursor = connection.cursor(buffered=True)
        query_part = self.database_name + '.' + self.table_name
        mysql_statement = "SELECT {0} FROM {1}".format('*', query_part)
        cursor.execute(mysql_statement)
        return cursor.column_names

    def _get_db_connection(self, host_name, user_name, user_password, port_num, _db_name=None):
        """
        _get_db_connection is called by this class as needed to operate the MySQL database.

        :param host_name: (ex. localhost, 192.168.1.227)
        :param user_name: (ex. bilbo)
        :param user_password: (ex. baggins)
        :param port_num: (ex. 3306, 50011)
        :param _db_name: (ex. database_12, best_database)
        :return: This function returns a connection to a MySQL database.

        WARNING: If the values in the default.ini file are not correct then this function will fail.
        """
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
    def _get_html_unescape(_string):
        clean_string = str(_string)
        clean_string = clean_string.lstrip('_')
        # unescape_string = html.unescape(clean_string)
        unescape_string = TextProcessor().get_clean_word(clean_string)
        for item in HTML_UNESCAPE_TABLE:
            unescape_string = unescape_string.replace(item, HTML_UNESCAPE_TABLE.get(item))
        print("_get_html_unescape: " + unescape_string)
        return unescape_string

    def _get_onehot_dataframe(self, _link_key):
        onehot_indices = self.get_onehot_list(_link_key)
        dataframe = pandas.DataFrame(onehot_indices).astype(str)
        dataframe = dataframe.transpose()
        dataframe.columns = self._get_onehot_words(onehot_indices)
        return dataframe

    def _get_onehot_words(self, _onehot_index_list):
        words = []
        for index in _onehot_index_list:
            word = OneHotWords().get_word(index)
            word = self._get_html_unescape(word)
            words.append(word)
        print('_get_onehot_words: ' + _onehot_index_list[0])
        return words

    @staticmethod
    def _replace_none(_lists):
        if type(_lists) == list and len(_lists) > 0:
            if type(_lists[0]) == list:
                for list_index in range(0, len(_lists)):
                    _lists[list_index] = ['None' if v is None else v for v in _lists[list_index]]
                    print('replace many')
            else:
                _lists = ['_None' if v is None else v for v in _lists]
        _lists = ['default']
        return _lists

    def delete_database(self, _database_name):
        mysql_drop_database = MYSQL_DROP_DATABASE.format(self.get_clean_key_string(_database_name))
        self._execute_mysql(mysql_drop_database)
        # print('delete_database: ' + _database_name)

    def delete_table(self, _table_name):
        mysql_drop_table = MYSQL_DROP_TABLE.format(self.get_clean_key_string(_table_name))
        self._execute_mysql(mysql_drop_table)  # print('delete_table: ' + _table_name)

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

    @staticmethod
    def get_clean_key_string(_string):
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
        # select_template = '''SELECT * FROM seminole_main.seminole_main where link_key = "jurney";'''
        # clean_link_key = str(re.sub(LEGAL_CHARACTERS, '_', clean_link_key.strip()))
        if _value is None:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name, LINK_KEY,
                                                                         self.get_clean_key_string(_link_key))
        else:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name,
                                                                         self.get_clean_key_string(_link_key),
                                                                         self.get_clean_key_string(_value))

        link_key_id = self._execute_mysql(select_sql)
        # print('get_id: ' + clean_link_key + ' = ' + str(row_number))
        if link_key_id is None:
            return 0
        else:
            print('get_id: ' + str(link_key_id))
            return link_key_id

    def get_onehot(self, _link_key, _use_column_names=True, _count_uses=False):
        """
        You must use OneHotDB.put_onehot() before using puts a sentence This method creates a pandas.DataFrame where
        :param _link_key: is the reference to the sentence
        :param _use_column_names: if True then sets column names to the words in OneHotWords()
        :param _count_uses: if True then the value in the column is then number is instances that the word appears in the sentence; Otherwise, the value in the column is True when the word is present in the sentence
        :return: a dataframe where each row is the 'id' for each word from OneHotWords(); if the sentence has a word then 1 is placed in the column corresponding to the word 'id'
        """
        test_link_key = _link_key.split(' ')
        try:
            first_value = test_link_key[0]
        except AttributeError as err:
            print(err.name)

        onehot_list = self.get_onehot_list(_link_key)
        onehot_list_dataframe = pandas.DataFrame(numpy.ones((1, len(onehot_list))), dtype=int)
        onehot_list_dataframe.columns = onehot_list
        onehot_dataframe = pandas.DataFrame(numpy.zeros((1, OneHotWords().get_row_count())), dtype=int)
        for column in range(1, len(onehot_dataframe.columns), 1):
            this_value = onehot_list.pop()
            if this_value.isdigit():
                word_index = int(this_value)
            else:
                word_index = 0

            # indices begin at 1 and dataframe begins at 0
            onehot_dataframe.iat[0, word_index - 1] = (1 if not _count_uses else onehot_dataframe.iat[0, word_index - 1] + 1)
            print('word index: ' + str(word_index))
        # print('get_onehot: ' + translated_value)
        if _use_column_names:
            words = OneHotWords().get_words()
            onehot_dataframe.columns = words
        print(onehot_dataframe)
        return onehot_dataframe

    def get_onehot_list(self, _link_key):
        """
        onehot_list is a list of the indices for the words in the sentence referenced by _link_key

        :param _link_key: references the row with the one-hot encoded value
        :return: returns a list of integers, where each integer is an index to a word in OneHotWords()
        """
        result = str(self.get(_link_key, 'sentence'))
        if result is None:
            return ['1', '2']
        result = result.lstrip('|')
        indices = result.split(',')
        index_list = []
        for index in indices:
            index_list.append(index)
        print('get_onehot: ' + _link_key)
        return index_list

    def get_onehot_matrix(self, _link_key):
        onehot_indices = self.get_onehot(_link_key)
        num_words = OneHotWords().get_row_count()
        onehot_matrix = numpy.zeros([1, 166], dtype=int)
        onehot_matrix_dataframe = pandas.DataFrame(onehot_matrix)

        print('get_onehot_matrix done!')
        return num_words

    def get_row_count(self):
        """
        Sometimes you need to know how many rows are in the table.
        :return: Returns the number of rows in self.table_name.
        """
        get_row_count_mysql = "SELECT COUNT(*) FROM {0};".format(self.table_name)
        row_count = self._execute_mysql(get_row_count_mysql)
        # print('get_row_count: ' + str(row_count[0]))
        return row_count[0]

    def get_row_number(self, _link_key, _key=None):
        # select_template = '''SELECT * FROM seminole_main.seminole_main where link_key = "jurney";'''
        # clean_link_key = str(re.sub(LEGAL_CHARACTERS, '_', clean_link_key.strip()))
        clean_link_key = self.get_clean_key_string(_link_key)
        if _key is None:
            select_sql = "SELECT id FROM {0} WHERE {1} = '{2}';".format(self.table_name, LINK_KEY, clean_link_key)
        else:
            clean_key = self.get_clean_key_string(_key)
            select_sql = "SELECT id FROM {0} WHERE {1} = '{2}';".format(self.table_name, LINK_KEY, clean_key)

        row_number = self._execute_mysql(select_sql)
        # print('get_id: ' + clean_link_key + ' = ' + str(row_number))
        if row_number is None:
            return 0
        else:
            return row_number

    def get_sentence_indices(self):
        dataframe = self.get_dataframe()
        link_keys = dataframe[LINK_KEY].values.tolist()
        # link_key_array = link_keys.
        print('get_sentence_indices done!')
        return link_keys

    def get_values(self, _link_key, _exclude_2=False):
        values = list(self.get(_link_key))
        if _exclude_2:
            values.pop(0)
            values.pop(0)
        return values

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
        open_database_mysql = MYSQL_CREATE_DATABASE.format(self.get_clean_key_string(_database_name))
        self._execute_mysql(open_database_mysql)
        self.open_table(self.table_name)
        print('open_database: ' + _database_name)

    def open_table(self, _table_name):
        # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
        self.table_name = self.get_clean_key_string(_table_name)
        # clean_table_name = self.get_clean_key_string(self.table_name)
        mysql_open_table = MYSQL_CREATE_TABLE.format(
            self.table_name, 'id', LINK_KEY)
        self._execute_mysql(mysql_open_table)
        # self._add_column('link_key')
        # print('open_table: ' + _table_name)

    @staticmethod
    def pickle_words(_filename_key=None):
        """
        This method pickles the words in OneHotWords using _filename_key
        :param _words_filename_key:
        :return:
        """
        words = OneHotWords().get_words()
        # pickle
        try:
            os.mkdir("../../data/words/")
        except FileExistsError:
            pass
        words_file_name = "../../data/words/" + ('default' if _filename_key is None else _filename_key) + ".onehotwords.pkl"
        words_dataframe = pandas.DataFrame(words)
        words_dataframe = words_dataframe.transpose()
        words_dataframe.to_pickle(words_file_name)
        print('pickle_words: ' + words_file_name)
        return words_dataframe

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
            link_key_id = self._copy_row(_link_key, _key_value)
        else:
            # sets value in the column _link_key_value to _key_value in the row where the link_key is _link_key
            if self.get_id(_link_key) == 0:
                self.put(_link_key)
            self._add_column(_key_value)
            link_key_id = self.update_value(_link_key, _key_value, TextProcessor().get_clean_word(_value))
        return link_key_id

    def put_onehot(self, _link_key, _string):
        words = _string.strip().split(' ')
        indices = []
        for word in words:
            if word != '':
                # clean_word = html.escape(word)
                clean_word = TextProcessor().get_clean_word(word)
                word_result = OneHotWords().put(clean_word)
                index = str(word_result)
                indices.append(index)
        combined_indices = ''
        for part in indices:
            combined_indices = combined_indices + part + ','
        combined_indices = combined_indices.rstrip(',')
        return self.put(_link_key, SENTENCE_KEY, combined_indices)

    @staticmethod
    def remove_none(_result):
        if _result is None:
            _result = 'None'
        if type(_result) == list:
            for index in range(0, len(_result), 1):
                if _result[index] is None:
                    _result[index] = 'None'
        return _result

    def update_value(self, _link_key, _key, _value):
        mysql_insert_statement = MYSQL_UPDATE_STATEMENT.format(self.table_name, self.get_clean_key_string(_key),
                                                               self.get_clean_key_string(_value), 'id',
                                                               self.get_id(_link_key))
        self._execute_mysql(mysql_insert_statement)
        return self.get_id(_link_key)


def test_delete_database():
    temp_onehotdb = OneHotDB()
    temp_onehotdb.delete_database('test_onehotdb')


def test_delete_table():
    onehotdb = OneHotDB()
    onehotdb.open_table('temp_table')
    onehotdb.delete_table('temp_table')
    print('test_delete_table done!')


def test_get_clean_key_string():
    KEY = "Instrument #"
    onehotdb = OneHotDB()
    clean_key = onehotdb.get_clean_key_string(KEY)
    print('test_get_clean_key_string: ' + clean_key)


def test_get_onehot():
    onehotdb = OneHotDB()
    second_key = onehotdb.get_onehot('first_key', _use_column_names=False)
    onehotdb.put_onehot('second_key', "That's not it?")
    second_key = onehotdb.get_onehot('second_key')
    second_key = onehotdb.get_onehot('second_key', _use_column_names=False)
    tmp_file = open('../../data/txt/shakespear.txt', 'r+')
    file_text = tmp_file.read()
    onehotdb.put_onehot('third_key', file_text)
    third_onehot = onehotdb.get_onehot('third_key', _count_uses=True, _use_column_names=False)
    print(third_onehot)
    print('test_get_onehot done!')


def test_get_onehot_matrix():
    onehotdb = OneHotDB()
    onehotdb.put_onehot('first_key', "Abra kadab'ro'")
    onehot_matrix = onehotdb.get_onehot_matrix('first_key')
    print('test_get_onehot_matrix done!')


def test_get_row_count():
    onehotdb = OneHotDB()
    row_count = onehotdb.get_row_count()
    print('test_get_row_count: ' + str(row_count))


def test_get_sentence_indices():
    onehotdb = OneHotDB()
    link_keys = onehotdb.get_sentence_indices()
    print('test_get_sentence_indices done!')
def test_init():
    onehotdb = OneHotDB()
    # print('test_init done!')


def test_put_onehot():
    onehotdb = OneHotDB()
    onehotdb.put_onehot('first_key', "Abra kadab'ro'")
    # onehotdb.put_onehot('second_key', '''This is an elegant approach, to do the search and replace using a <code>formatter</code>. However, if I hadn't seen @Martijn Pieters answer it would be a bit mysterious, so I will mark his as the accepted answer since it has more explanation. Richard Neish Feb 28, 2013 at 15:19 ''')

    first_key_value = onehotdb.get_onehot_list('first_key')
    print('test_put_onehot get_onehot: ' + first_key_value[0])


def test_to_pickle():
    onehotdb = OneHotDB()
    onehotdb.pickle_words('word_key')
    print('test_to_pickle done!')



# edit configuration /etc/mysql/mysql.conf.d/mysqld.cnf to change bind-address/127.0.0.1 and port/3306
# configuration edits require terminal commands: sudo service mysql stop, start, status

# To use mysql from a terminal: mysql, sudo mysql, sudo mysql -u root -p
# SHOW DATABASES;
# If missing iriyedb then create using mysql: CREATE DATABASE iriyedb;
# Show All Users: SELECT user,authentication_string,plugin,host FROM mysql.user;
# If bilbo is not present then use mysql command: create user 'bilbo'@'127.0.0.1' identified by 'baggins';
#   GRANT ALL PRIVILEGES ON *.* TO 'bilbo'@'127.0.0.1' WITH GRANT OPTION;
#   show grants for 'bilbo'@'127.0.0.1';
# repeat the above process for any other user/pw combo
# CREATE onehotdb_table users
# (
#   id              INT unsigned NOT NULL AUTO_INCREMENT,
#   username        VARCHAR(150) NOT NULL,
#   password        VARCHAR(150) NOT NULL,
#   birth           DATE NOT NULL,
#   PRIMARY KEY     (id)
# );
# INSERT INTO users ( username, password, birth) VALUES
#   ( 'bilbo', 'baggins', '2015-01-03' ),
#   ( 'john', 'doe', '2013-11-13' );
# Install mysql with the following commands:
#   sudo rm -rf /var/lib/mysql/mysql
#   sudo apt-get remove --purge mysql-server mysql-client mysql-common
#   sudo apt-get autoremove
#   sudo apt-get autoclean
#   sudo apt-get install mysql-server
# import pickle5 as pickle is used to convert formats when pkl files are from an older version
if __name__ == '__main__':
    test_init()

    test_put_onehot()

    test_get_onehot_matrix()
    test_delete_table()
    test_delete_database()
    test_get_row_count()
    test_get_clean_key_string()
    test_get_onehot()
    test_get_sentence_indices()
    test_to_pickle()

    # the following line is not reached because of sys.exit() in python()
    print("python done!")
