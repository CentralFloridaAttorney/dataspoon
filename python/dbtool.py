import html
import os

import mysql
import pandas
from mysql.connector import Error

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
# HOST = '192.168.1.227'
HOST = 'localhost'
USER = 'bilbo'
PASSWD = 'baggins'
PORT = '3306'
DB_NAME = 'dbtool'
DEFAULT_TABLE_NAME = 'default_table'
LEGAL_CHARACTERS = r"[^'a-zA-Z0-9\s\·\,\.\:\:\(\)\[\]\\\\]]"
ILLEGAL_WORDS = ['True']
LINK_KEY = 'link_key'
FORBIDDEN_DATABASES = ['users']
HTML_ESCAPE_TABLE = {
    "&": "&amp;",
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
UPDATE_STATEMENT = "UPDATE {0} SET {1} = '{2}' WHERE {3} = '{4}';"
HASH_MOD = 1
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ONEHOT_DB_NAME = 'onehotwords'
ONE_HOT_WORD_TABLE_NAME = 'words'
ONEHOT_KEY = 'sentence'
DEFAULT_PKL_INPUT = '../data/users.pkl'
DEFAULT_PKL_OUTPUT = '../data/output.pkl'


class DBTool:
    def __init__(self, _database_name=None, _table_name=None):
        """
        DBTool() provides access to MySQL functions within Python.

        :param _database_name: Optionally, specify self.database_name
        :param _table_name: Optionally, specify self.table_name

        To open the default database:

        dbtool = DBTool()

        To open a database named 'xyzzydb'

        xyzzydb = DBTool('xyzzydb')

        To open a database named 'xyzzydb' and a table named 'magic_table'

        xyzzydb = DBTool('xyzzydb', 'magic_table')

        """
        self.base_dir = ROOT_DIR.rsplit('/', 1)[0] + '/'
        if _database_name is None:
            self.database_name = DB_NAME
        else:
            self.database_name = self.get_clean_key(_database_name)
        if _table_name is None:
            self.table_name = DEFAULT_TABLE_NAME
        else:
            self.table_name = self.get_clean_key(_table_name)
        self.open_database(self.database_name)
        # self.open_table(self.table_name)
        # print('__init__ done!')

    def _add_column(self, _column_name):
        """
        DBTool._add_column() adds a column your MySQL database table
        :param _column_name: name of the new column
        """
        query = "ALTER TABLE {0} ADD {1} VARCHAR(4096);".format(self.table_name, self.get_clean_key(_column_name))
        # values = [self.table_name, self.get_clean_key(_column_name)]

        self._execute_mysql(query)
        # print('Add column: '+ _column_name)

    def _execute_mysql(self, _mysql_statement, _value=None):
        """
        DBTool._execute_mysql() executes MySQL commands, which are called by other methods.
        :param _mysql_statement: a formatted string with a MySQL command.
        :param _value: RESERVED for future use
        :return: returns the result of the MySQL statement or an error message.
        """
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
                    result = cursor.fetchone()
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

    @staticmethod
    def _get_html_escape(_string):
        # clean_string = str(_string)
        # print("***** test: " + clean_string)
        clean_string = "".join(HTML_ESCAPE_TABLE.get(c, c) for c in str(_string))
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

    def _get_columns(self):
        connection = self._get_db_connection(HOST, USER, PASSWD, PORT, self.database_name)
        cursor = connection.cursor(buffered=True)
        mysql_statement = "SELECT * FROM {0};".format(self.table_name)
        cursor.execute(mysql_statement)
        return cursor.column_names

    def add_dataframe(self, _data_frame, _link_key_column_num=0):
        # when adding a dataframe each row requires a link_key
        # the link_key is the row_number of the newly added record
        h, w = _data_frame.shape
        for row in range(0, h, 1):
            link_key = str(_data_frame.iloc[row][_link_key_column_num])
            for column in range(0, w, 1):
                key = str(_data_frame.columns[column])
                value = str(_data_frame.iloc[row][column])
                self.put(link_key, key, value)
        # print('add_dataframe done!')

    def delete_database(self, _database_name):
        mysql_drop_database = "DROP DATABASE {0}".format(self.get_clean_key(_database_name))
        self._execute_mysql(mysql_drop_database)
        # print('delete_database: ' + _database_name)

    def delete_table(self, _table_name):
        mysql_drop_table = "DROP TABLE {0}".format(self.get_clean_key(_table_name))
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
            sql_statement = SELECT_STATEMENT.format('*', self.table_name, LINK_KEY, self.get_clean_key(_link_key))
        else:
            # 2 result: returns the value for key on the link_key row
            self._add_column(_link_key)
            sql_statement = SELECT_STATEMENT.format(self.get_clean_key(_key), self.table_name, LINK_KEY,
                                                    self.get_clean_key(_link_key))
        result = self._execute_mysql(sql_statement)
        return result

    @staticmethod
    def get_clean_key(_string=str):
        """
        DBTool().get_clean_key() replaces certain characters with web entity values or escape codes.

        :param _string: a string value
        :return: returns a value that is suitable for being used as a name in MySQL

        MySQL has rules about what values can be in an identifier. This method processes string values to comply with the rules.

        clean_value = DBTool().get_clean_key("That's great!")

        clean_value = 'That&apos;s&nbspa&nbspgreat!'
        """
        if _string.isdigit():
            _string = "_" + str(_string)
        # _string = "".join(HTML_ESCAPE_TABLE.get(c, c) for c in str(_string))
        _string = html.escape(_string)
        return _string

    def get_row_count(self):
        """
        Sometimes you need to know how many rows are in the table.
        :return: Returns the number of rows in self.table_name.
        """
        get_row_count_mysql = "SELECT COUNT(*) FROM {0};".format(self.table_name)
        row_count = self._execute_mysql(get_row_count_mysql)
        # print('get_row_count: ' + str(row_count[0]))
        return row_count[0]

    def get_row_number(self, _link_key, _value=None):
        """
        DBTool.get_row_number() returns a row number for either a link_key or key/value pair.
        :param _link_key: _link_key uniquely identifies the row.
        :param _value: _key is an optional parameter, which is used to identify the column name.
        :return: If _key=None then return the row_number where link_key = _link_key.  Otherwise, return the ro_number where a key/value pair matches _link_key/_key_value.
        """
        # select_template = '''SELECT * FROM seminole_main.seminole_main where link_key = "jurney";'''
        # clean_link_key = str(re.sub(LEGAL_CHARACTERS, '_', clean_link_key.strip()))
        if _value is None:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name, LINK_KEY, self.get_clean_key(_link_key))
        else:
            select_sql = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('id', self.table_name, self.get_clean_key(_link_key), self.get_clean_key(_value))

        row_number = self._execute_mysql(select_sql)
        # print('get_row_number: ' + clean_link_key + ' = ' + str(row_number))
        if row_number is None:
            return 0
        else:
            print('get_row_number: ' + str(row_number))
            return row_number

    def open_database(self, _database_name, _table_name=None):
        # self.database_name = str(re.sub(LEGAL_CHARACTERS, '_', _database_name.strip()))
        self.database_name = self.get_clean_key(_database_name)
        if _table_name is not None:
            # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
            self.table_name = self.get_clean_key(_table_name)

        # When you open_database self.table_name does not change
        # self.table is used in: _add_column, get, get_row_number, open_table, add_dataframe, and put
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
        # clean_table_name = self.get_clean_key(self.table_name)
        mysql_open_table = "CREATE TABLE {0} (id int(10) NOT NULL AUTO_INCREMENT, ".format(self.table_name)
        mysql_open_table += LINK_KEY + " varchar(255), PRIMARY KEY (id));"
        self._execute_mysql(mysql_open_table)
        # self._add_column('link_key')
        # print('open_table: ' + _table_name)



    def to_pickle(self, _file_path):
        mysql_statement = "SELECT * FROM {0}".format(self.table_name)
        result = self._execute_mysql(mysql_statement)
        columns = self._get_columns()
        dataframe = pandas.DataFrame(result)
        dataframe = dataframe.transpose()
        dataframe.columns = columns
        dataframe.to_pickle(self.base_dir + _file_path)
        print('to_pickle: ' + self.base_dir + _file_path)

    def put(self, _link_key, _link_key_value=None, _key_value=None, _value=None):
        """
        DBTool().put() inserts values and returns the row_number of the affected record.

        DBTool().put() behaves differently depending upon the number of parameters that are passed:
            1) adds a row with link_key = _link_key
            2) changes the value of _link_key = _link_key_value
            3) sets value in the column _link_key_value to _key_value in the row where the link_key is _link_key
            4) sets value in the column _key_value to _value in the row where the column _link_key is _link_key_value

        :param _link_key: up to 3 parameters is link_key; otherwise, is column name to find _link_key_value
        :param _link_key_value: if 2 parameters then replaces link_key where link_key = _link_key; if 3 parameters then is column name where _key_value will be placed; if 4 parameters then is the value to match in column _link_key.
        :param _key_value: if 3 parameters then is the value for column named _link_key_value; otherwise, is column name for _value
        :param _value: is the value to be placed in column named _key_value, where a column named _link_key = _link_key_value
        :return: returns the row_number of the affected row
        """
        # returns row_number of _link_key
        # 1 value: new_link_key
        # 2 value: old_link_key_value, new_link_key_value
        # 3 value: link_key, key, value
        result = 'default'
        if _link_key_value is None:
            row_number = self.get_row_number(_link_key)
            # returns the row_number from mysql_statement = select all from table_name where LINK_KEY is _link_key
            mysql_statement = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format('*', self.table_name, LINK_KEY,self.get_clean_key(_link_key))
            if row_number == 0:
                # add a link_key = _link_key
                mysql_statement = "INSERT INTO {0} ({1}) VALUES ('{2}');".format(self.table_name,
                                                                                 LINK_KEY,
                                                                                 self.get_clean_key(_link_key))
            result = self.get_row_number(_link_key)
        elif _key_value is None:
            # mysql_statement = update table_name set LINK_KEY to _link_key_value where id is row_number of _link_key
            # does _link_key exist
            row_number = self.get_row_number(_link_key)
            if row_number == 0:
                mysql_statement = "INSERT INTO {0} ({1}) VALUES ('{2}');".format(self.table_name,
                                                                                 LINK_KEY,
                                                                                 self.get_clean_key(_link_key))
            else:
                mysql_statement = UPDATE_STATEMENT.format(self.table_name,
                                                          LINK_KEY,
                                                          self.get_clean_key(_link_key_value),
                                                          'id',
                                                          self.get_row_number(_link_key))
            result = self.get_row_number(_link_key_value)
        elif _value is None:
            self.put(_link_key)
            self._add_column(_link_key_value)
            # mysql_statement = update table_name set _link_key_value = _key_value where id is row number of _link_key
            mysql_statement = UPDATE_STATEMENT.format(self.table_name,
                                                      self.get_clean_key(_link_key_value),
                                                      self.get_clean_key(_key_value),
                                                      'id',
                                                      self.get_row_number(_link_key))
            result = self.get_row_number(_link_key)
        else:
            row_number = self.get_row_number(_link_key, _link_key_value)
            # if row_number == 0 then create a new row with _link_key as the value for column and link_key:
            #   1) add a row with link_key = _link_key
            #   2) set the value of a column named _link_key to _link_key_value
            #   3) set the value of a column named _key_value to _value
            if row_number == 0:
                self.put(_link_key)
                self._add_column(_link_key)
                self.put(_link_key, _link_key, _link_key_value)
            # mysql_statement = update table_name set _key_value = _value where _link_key is _link_key_value.
            self._add_column(_key_value)
            mysql_statement = UPDATE_STATEMENT.format(self.table_name,
                                                      self.get_clean_key(_key_value),
                                                      self.get_clean_key(_value),
                                                      self.get_clean_key(_link_key),
                                                      self.get_clean_key(_link_key_value))
            result = self.get_row_number(_link_key)

        self._execute_mysql(mysql_statement)
        # print('put: ')
        return result


class OneHotWords(DBTool):
    # mysql has a maximum number of 4096 columns per table
    # Therefore, each sentence has a maximum number of words
    def __init__(self):
        super().__init__(ONEHOT_DB_NAME, ONE_HOT_WORD_TABLE_NAME)
        # print('__init__ done!')

    def get_word(self, _index):
        sql_statement = "SELECT link_key FROM {0} WHERE id = '{1}';".format(self.table_name, str(_index))
        this_word = self._execute_mysql(sql_statement)
        # print('get_word done!')
        return this_word

    def get_index(self, _word):
        # This function returns the row number of _word in the onehot index
        clean_word = self.get_clean_key(_word)
        row_number = super().get_row_number(clean_word)
        return row_number


def test_put():
    # dbtool = DBTool()
    dbtool = DBTool('dbtool_test_db', 'dbtool_test_table')
    row_1 = dbtool.put('value_1a')
    row_2 = dbtool.put('value_1a', 'value_2b') # creates link_key ('xyzzy') and puts key/value ('failures'/'543')
    row_3 = dbtool.put('value_3a', 'value_3b', 'value_3c') # creates link_key ('new_link_key')
    row_4 = dbtool.put('value_4a', 'value_4b', 'value_4c', 'value_4d')
    # python.put('put_2')
    # python.put('put_2', 'failures', '345')
    # python.put('put_1', 'xyzzy')

    # python.put('old_index_1', "old_index_2")
    # if link_key/word_1 does not exist then creates link_key/word_1 and renames link_key to word_1a
    # if link_key for word_1 does exist then this changes link_key/word_1 to word_1a
    # python.put('word_1', 'word_1a')
    # sets key/word_1 to value/word_1a in row with link_key/word_1b
    # python.put('word_1', 'word_1a', 'word_1b')
    print('test_put done!')


def test_get():
    dbtool = DBTool('dbtool_test_db', 'dbtool_test_table')
    link_key_index = dbtool.get('xyzzy') # returns row_number of link_key ('xyzzy')
    dbtool.put('xyzzy', 'failures', '2469')
    value = dbtool.get('xyzzy', 'failures')
    print('index of put_2 from test_get(): ' + str(link_key_index))
    # link_key_update_status = python.get('put_1', 'reput_1')
    print('***** value: ' + value)


def test_get_row_count():
    dbtool = DBTool()
    row_count = dbtool.get_row_count()
    print('test_get_row_count: ' + str(row_count))


def test_get_clean_key():
    KEY = "Instrument #"
    dbtool = DBTool()
    clean_key = dbtool.get_clean_key(KEY)
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
    dbtool.to_pickle('data/mysql.pkl')
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
    row_number_1 = dbtool.get_row_number('xyzzy')
    row_number_2 = dbtool.get_row_number('new_link_key')
    row_number_3 = dbtool.get_row_number('failures', '543')
    row_number_4 = dbtool.get_row_number('failures', '123')
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


if __name__ == '__main__':
    # onehotwords
    # test_onehotwords()

    # dbtool
    # test_static_operation()
    # test_get_html_unescape()
    # test_init()
    test_put()
    #test_get()
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
    print("python done!")
