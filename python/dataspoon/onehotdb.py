import html
import os

import mysql
import pandas
from mysql.connector import Error

from python.dataspoon.dbtool import OneHotWords

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
# CREATE ONE_HOT_WORD_TABLE_NAME users
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
HOST = 'localhost'
# HOST = '192.168.1.227'
USER = 'bilbo'
PASSWD = 'baggins'
PORT = '3306'
DB_NAME = 'onehotdb'
TABLE_NAME = 'sentences'
LEGAL_CHARACTERS = r"[^'a-zA-Z0-9\s\·\,\.\:\:\(\)\[\]\\\\]]"
ILLEGAL_WORDS = ['True']
LINK_KEY = 'link_key'
FORBIDDEN_DATABASES = ['users']
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
SELECT_STATEMENT = "SELECT {0} FROM {1} WHERE {2} = '{3}';"
HASH_MOD = 1
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)).rsplit('/', 1)[0] + '/'
ONEHOT_DB_NAME = 'onehot_tool'
ONE_HOT_WORD_TABLE_NAME = 'test_dict'
SENTENCE_KEY = 'sentence'


# PKL_PATH = '/home/overlordx/PycharmProjects/SeminoleScraper/data/pkl'
# DIR_PATH = r'/home/overlordx/PycharmProjects/SeminoleScraper/data/cases/seminole/10_7_2022'

class OneHotDB:
    def __init__(self, _database_name=None, _table_name=None):
        self.base_dir = ROOT_DIR.rsplit('/', 1)[0] + '/'
        # TODO: make table for key storage
        if _database_name is None:
            self.database_name = DB_NAME
        else:
            self.database_name = self.get_clean_key(_database_name)
        if _table_name is None:
            self.table_name = TABLE_NAME
        else:
            self.table_name = self.get_clean_key(_table_name)
        self.open_database(self.database_name)
        # self.open_table(self.table_name)
        # print('__init__ done!')

    def _execute_mysql(self, _mysql_statement, _value=None):
        result = 'default'
        try:
            connection = self._get_db_connection(HOST, USER, PASSWD, PORT, self.database_name)
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

    def _get_db_connection(self, host_name, user_name, user_password, port_num, _db_name=None):
        connection = None
        try:
            if _db_name is not None:
                connection = mysql.connector.connect(
                    host=host_name,
                    user=user_name,
                    passwd=user_password,
                    port=port_num,
                    database=self.get_clean_key(_db_name)
                )
                self.database_name = self.get_clean_key(_db_name)
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
                    host=HOST,
                    user=USER,
                    passwd=PASSWD,
                    port=PORT,
                    database='sys'
                )
                try:
                    cursor = connection.cursor(buffered=True)
                    mysql_create_database = "CREATE DATABASE {0};".format(self.get_clean_key(_db_name))
                    cursor.execute(mysql_create_database)
                    connection.commit()
                    self.database_name = self.get_clean_key(_db_name)
                    # print("_get_db_connection created database: " + db_name)
                except Error as err:
                    print(f"Error: '{err}'")
            else:
                print('_get_db_connection error: ' + _db_name)
                # print('created new database: ' + db_name)
        return connection

    def _get_columns(self):
        connection = self._get_db_connection(HOST, USER, PASSWD, PORT, self.database_name)
        cursor = connection.cursor(buffered=True)
        mysql_statement = "SELECT * FROM {0}".format(self.database_name + '.' + self.table_name)
        cursor.execute(mysql_statement)
        return cursor.column_names

    @staticmethod
    def _get_html_escape(_string):
        clean_string = str(_string)
        if clean_string.isdigit():
            clean_string = "_" + clean_string
        escape_string = html.escape(clean_string)
        print("_get_html_escape: " + escape_string)
        return escape_string

    @staticmethod
    def _get_html_unescape(_string):
        clean_string = str(_string)
        clean_string = clean_string.lstrip('_')
        unescape_string = html.unescape(clean_string)
        for item in HTML_UNESCAPE_TABLE:
            unescape_string = unescape_string.replace(item, HTML_UNESCAPE_TABLE.get(item))
        print("_get_html_unescape: " + unescape_string)
        return unescape_string

    def get_clean_key(self, key):
        clean_key = self._get_html_escape(key)
        if clean_key.isdigit():
            clean_key = '_' + clean_key
        return clean_key

    def get_row_count(self):
        get_row_count_mysql = "SELECT COUNT(*) FROM " + self.table_name + ";"
        row_count = self._execute_mysql(get_row_count_mysql)
        # print('get_row_count: ' + str(row_count[0]))
        return row_count[0]

    def open_database(self, _database_name, _table_name=None):
        # self.database_name = str(re.sub(LEGAL_CHARACTERS, '_', _database_name.strip()))
        self.database_name = self.get_clean_key(_database_name)
        if _table_name is not None:
            # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
            self.table_name = self.get_clean_key(_table_name)

        # When you open_database self.table_name does not change
        # self.table is used in: _add_column, get, get_id, open_table, add_dataframe, and put
        # The default value for self.table_name is python
        # Therefore, _table_name may be required for open_database

        # self.database_name = _database_name
        # open_table_mysql = "CREATE TABLE " + self.table_name + "(id int(10) NOT NULL AUTO_INCREMENT," + LINK_KEY + " varchar(255), PRIMARY KEY (id))"
        open_database_mysql = "CREATE DATABASE {0};".format(self.get_clean_key(_database_name))
        opened_db = self._execute_mysql(open_database_mysql)
        self.open_table(self.table_name)
        print('open_database: ' + _database_name)

    def open_table(self, _table_name):
        # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
        self.table_name = self.get_clean_key(_table_name)
        # clean_table_name = self.get_clean_key_string(self.table_name)
        mysql_open_table = "CREATE TABLE {0} (id int(10) NOT NULL AUTO_INCREMENT, ".format(self.table_name)
        mysql_open_table += LINK_KEY + " varchar(255), PRIMARY KEY (id));"
        self._execute_mysql(mysql_open_table)
        # self._add_column('link_key')
        # print('open_table: ' + _table_name)

    def _add_column(self, _column_name):
        query = "ALTER TABLE {0} ADD {1} VARCHAR(4096);".format(self.table_name, self.get_clean_key(_column_name))
        # values = [self.table_name, self.get_clean_key_string(_column_name)]

        self._execute_mysql(query)
        # print('Add column: '+ _column_name)

    def delete_database(self, _database_name):
        mysql_drop_database = "DROP DATABASE {0}".format(self.get_clean_key(_database_name))
        self._execute_mysql(mysql_drop_database)
        # print('delete_database: ' + _database_name)

    def delete_table(self, _table_name):
        mysql_drop_table = "DROP TABLE '{0}'/.'{1}';".format(self.database_name,
                                                             self.get_clean_key(_table_name))
        result = self._execute_mysql(mysql_drop_table)  # print('delete_table: ' + _table_name)
        print('delete_table done!')

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
            sql_statement = SELECT_STATEMENT.format('*', self.table_name, LINK_KEY, self.get_clean_key(_link_key))
        else:
            # 2 result: returns the value for key on the link_key row
            self._add_column(_key)
            sql_statement = SELECT_STATEMENT.format(self.get_clean_key(_key),
                                                    self.table_name,
                                                    LINK_KEY,
                                                    self.get_clean_key(_link_key))
        result = self._execute_mysql(sql_statement)
        return result

    def _get_old(self, _link_key, _key=None, _value=None):
        if _key is None:
            # 1 result: link_key returns row for link_key
            self._add_column(LINK_KEY)
            sql_statement = SELECT_STATEMENT.format('*', self.table_name, LINK_KEY, self.get_clean_key(_link_key))
        elif _value is None:
            # 2 result: link_key, value returns the value
            self._add_column(self.get_clean_key(_link_key))
            sql_statement = SELECT_STATEMENT.format(self.get_clean_key(_key), self.table_name, LINK_KEY,
                                                    self.get_clean_key(_link_key))
        else:
            # 3 result: _key_value, _link_key, _key_value returns row_number of link_key
            sql_statement = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format(self.get_clean_key(_key), self.table_name,
                                                                            self.get_clean_key(_link_key),
                                                                            self.get_clean_key(_value))
        result = self._execute_mysql(sql_statement)
        if result is None:
            result = 'default'
        return result

    def _put(self, _link_key, _key_value=None, _value=None):
        # convert _link_key to onehot_link_key
        # returns row_number of _link_key
        # 1 value: link_key
        # 2 value: clean_key, value
        # 3 value: link_key, key, value
        result = 'default'
        if _key_value is None:
            row_number = self.get_row_number(_link_key)
            mysql_statement = "SELECT * FROM {0} WHERE {1} = {2};".format(self.table_name, LINK_KEY,
                                                                          self.get_clean_key(_link_key))
            if row_number == 0:
                # add a link_key = _link_key
                mysql_statement = "INSERT INTO {0} ({1}) VALUES ('{2}');".format(self.table_name, LINK_KEY,
                                                                                 self.get_clean_key(_link_key))
            result = [self.get_row_number(_link_key), _link_key]
            # mysql_statement = "INSERT INTO {0}"
        elif _value is None:
            # copies the value of link_key/_link_key to link_key/_link_key_value
            row_value = self._get(self.get_clean_key(_link_key))
            columns = self._get_columns()
            mysql_statement = "UPDATE {0} SET ({1}) = '{2}' WHERE {3} = '{4}';".format(self.table_name, LINK_KEY,
                                                                                       self.get_clean_key(_link_key),
                                                                                       LINK_KEY,
                                                                                       self.get_clean_key(_link_key))
            self._put(self.get_clean_key(_link_key))
            # self._add_column(self.get_clean_key_string(_link_key_value))
            row_number = self.get_row_number(self.get_clean_key(_link_key))
            mysql_statement = "UPDATE {0} SET {1} = '{2}' WHERE id = '{3}';".format(self.table_name, LINK_KEY,
                                                                                    self.get_clean_key(_key_value),
                                                                                    row_number)
        else:
            # update set _link_key_value = _key_value where id = row_number/link_key
            self._put(self.get_clean_key(_link_key))
            self._add_column(self.get_clean_key(_key_value))
            row_number = self.get_row_number(self.get_clean_key(_link_key))
            mysql_statement = "UPDATE {0} SET {1} = '{2}' WHERE id = '{3}';".format(self.table_name,
                                                                                    self.get_clean_key(_key_value),
                                                                                    self.get_clean_key(_value),
                                                                                    row_number)
        self._execute_mysql(mysql_statement)
        # print('put: ')
        result = self.get_row_number(_link_key)

        return result

    def get_onehot_list(self, _link_key):
        """

        :param _link_key: references the row with the one-hot encoded value
        :return: returns a list of integers, where each integer is an index to a word in OneHotWords()
        """
        result = self.get(_link_key, 'sentence')
        if result is None:
            return ['1', '2']
        result = result.lstrip('|')
        indices = result.split(',')
        index_list = []
        for index in indices:
            index_list.append(index)
        print('get_onehot: ' + _link_key)
        return index_list

    def _get_onehot_words(self, _onehot_index_list):
        words = []
        for index in _onehot_index_list:
            word = OneHotWords().get_word(index)
            word = self._get_html_unescape(word)
            words.append(word)
        print('_get_onehot_words: ' + _onehot_index_list[0])
        return words

    def get_onehot_dataframe(self, _link_key):
        onehot_indices = self.get_onehot_list(_link_key)
        dataframe = pandas.DataFrame(onehot_indices).astype(str)
        dataframe = dataframe.transpose()
        dataframe.columns = self._get_onehot_words(onehot_indices)
        return dataframe

    def put_onehot(self, _link_key, _string):
        words = _string.strip().split(' ')
        indices = []
        for word in words:
            if word != '':
                clean_word = html.escape(word)
                word_result = OneHotWords().put(clean_word)
                index = str(word_result)
                indices.append(index)
        combined_indices = '|'
        for part in indices:
            combined_indices = combined_indices + part + ','
        combined_indices = combined_indices.rstrip(',')
        clean_link_key = self.get_clean_key(_link_key)
        self._put(clean_link_key, SENTENCE_KEY, combined_indices)
        # print('put_onehot: ' + self.get_clean_key_string(_link_key) + combined_indices)
        return combined_indices

    def get_row_number(self, _link_key, _key=None):
        # select_template = '''SELECT * FROM seminole_main.seminole_main where link_key = "jurney";'''
        # clean_link_key = str(re.sub(LEGAL_CHARACTERS, '_', clean_link_key.strip()))
        clean_link_key = self.get_clean_key(_link_key)
        if _key is None:
            select_sql = "SELECT id FROM {0} WHERE {1} = '{2}';".format(self.table_name, LINK_KEY, clean_link_key)
        else:
            clean_key = self.get_clean_key(_key)
            select_sql = "SELECT id FROM {0} WHERE {1} = '{2}';".format(self.table_name, LINK_KEY, clean_key)

        row_number = self._execute_mysql(select_sql)
        # print('get_id: ' + clean_link_key + ' = ' + str(row_number))
        if row_number is None:
            return 0
        else:
            return row_number

    def add_dataframe(self, _data_frame, _link_key_column_num=0):
        # when adding a dataframe each row requires a link_key
        # the link_key is the row_number of the newly added record
        # must implement
        h, w = _data_frame.shape
        for row in range(0, h, 1):
            link_key = str(_data_frame.iloc[row][_link_key_column_num])
            for column in range(0, w, 1):
                key = str(_data_frame.columns[column])
                value = str(_data_frame.iloc[row][column])
                self._put(self.get_clean_key(link_key), self.get_clean_key(key), self.get_clean_key(value))
        # print('add_dataframe done!')

    def add_pickle(self, _pkl_path, _table_name=None):
        dataframe = pandas.read_pickle(_pkl_path)
        if _table_name is not None:
            self.open_table(_table_name)
        self.add_dataframe(dataframe)
        print('add_pickle: ' + _pkl_path)

    def get_onehot(self, _link_key):
        test_link_key = _link_key.split(' ')
        try:
            first_value = test_link_key[0]
        except AttributeError as err:
            print(err.name)

        onehot_dataframe = self.get_onehot_list(_link_key)
        translated_value = ''
        for index in onehot_dataframe:
            this_word = OneHotWords().get_word(index)
            this_word = html.unescape(this_word)
            # html.escape() does not seem to work this_word may contain unescaped codes
            for item in HTML_UNESCAPE_TABLE:
                this_word = this_word.replace(item, HTML_UNESCAPE_TABLE.get(item))
            clean_word = "".join(HTML_UNESCAPE_TABLE.get(c, c) for c in this_word)
            translated_value = translated_value + " " + clean_word
        print('get_translated_value: ' + translated_value)
        return translated_value

    def to_pickle(self, _file_path):
        mysql_statement = "SELECT * FROM {0}".format(self.table_name)
        result = self._execute_mysql(mysql_statement)
        columns = self._get_columns()
        dataframe = pandas.DataFrame(result)
        # dataframe = dataframe.transpose()
        dataframe.columns = columns
        dataframe.to_pickle(_file_path)
        print('to_pickle: ' + _file_path)


def create_dataframe():
    data = [['bilbo', 'thoron'], ['baggins', 'falbright']]
    data_frame = pandas.DataFrame(data)
    data_frame = data_frame.transpose()
    columns = ['username', 'password']
    data_frame.columns = columns
    data_frame.to_pickle('../../data/users.pkl')
    return data_frame


def test_init():
    onehotdb = OneHotDB('test_onehotdb', 'put_word_table')
    # print('test_init done!')


def test_get_row_count():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    row_count = onehotdb.get_row_count()
    print('test_get_row_count: ' + str(row_count))


def test_get_clean_key():
    KEY = "Instrument #"
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    clean_key = onehotdb.get_clean_key(KEY)
    print('test_get_clean_key: ' + clean_key)


def test_add_data_frame():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    onehotdb.add_dataframe(create_dataframe())
    print('test_add_dataframe: ')


def test_add_pickle():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    onehotdb.add_pickle('../../data/pkl/CaseGrid.pkl', 'case_grid')

    print('test_sql2pkl done!')


def test_get_unescape():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    string_value = '''This is the "best" test of the * everything & nothing.'''
    escaped_string = html.escape(string_value)
    unescaped_string = html.unescape(escaped_string)
    print("test_get_unescape: \n" + unescaped_string + "\n ***** \n" + escaped_string)


def test_get_onehot():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    onehotdb.put_onehot('second_key', '''
spark ml StringIndexer vs OneHotEncoder, when to use which?https://datascience.stackexchange.com › questions › spa...
Jan 17, 2022 — I don't see many people using StringIndexer, when indexing, but see OneHot as the primary form for categorical indexing. Share.''')
    onehot_indices = onehotdb.get_onehot_list('first_key')
    onehot_dataframe = onehotdb.get_onehot_dataframe('first_key')
    translated_value_1 = onehotdb.get_onehot('first_key')
    print('test_get_onehot: ' + translated_value_1)


def test_get_onehot_dataframe():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    onehotdb.put_onehot('first_key', '''Transform Data - Amazon SageMaker - AWS Documentationhttps://docs.aws.amazon.com › data-wrangler-transform
The Data Wrangler categorical encoders create encodings for all categories that exist in a column at the time the step is defined. If new categories have been ...''')
    dataframe = onehotdb.get_onehot_dataframe('first_key')
    print('test_get_onehot_dataframe done!')


def test_put_onehot():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    onehotdb.put_onehot('first_key', "Abra kadab'ro'")
    onehotdb.put_onehot('second_key',
                        '''This is an elegant approach, to do the search and replace using a <code>formatter</code>. However, if I hadn't seen @Martijn Pieters answer it would be a bit mysterious, so I will mark his as the accepted answer since it has more explanation. Richard Neish Feb 28, 2013 at 15:19 ''')

    first_key_value = onehotdb.get_onehot_list('first_key')
    print('test_put_onehot get_onehot: ' + first_key_value[0])


def test_to_pickle():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    onehotdb.to_pickle('../../data/put_word_table.pkl')
    print('test_to_pickle done!')


def test_delete_database():
    temp_onehotdb = OneHotDB('test_onehotdb')
    temp_onehotdb.delete_database('test_onehotdb')


def test_delete_table():
    onehotdb = OneHotDB('test_onehotdb', 'test_onehotdb_table')
    onehotdb.open_table('temp_table')
    onehotdb.delete_table('temp_table')
    print('test_delete_table done!')


if __name__ == '__main__':
    test_delete_table()
    test_delete_database()
    test_init()
    test_get_row_count()
    test_add_data_frame()
    test_get_clean_key()
    test_get_unescape()
    test_put_onehot()
    test_get_onehot()
    test_get_onehot_dataframe()
    test_add_pickle()
    test_to_pickle()
    # the following line is not reached because of sys.exit() in python()
    print("python done!")
