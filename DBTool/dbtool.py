import base64
import hashlib
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
HOST = 'localhost'
USER = 'bilbo'
PASSWD = 'baggins'
PORT = '3306'
DB_NAME = 'dbtool'
TABLE_NAME = 'dbtool'
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
SELECT_STATEMENT = "SELECT {0} FROM {1} WHERE {2} = '{3}';"
HASH_MOD = 1
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ONEHOT_DB_NAME = 'onehot_words'
ONE_HOT_WORD_TABLE_NAME = 'words'
ONEHOT_KEY = 'sentence'
# PKL_PATH = '/home/overlordx/PycharmProjects/SeminoleScraper/data/pkl'
# DIR_PATH = r'/home/overlordx/PycharmProjects/SeminoleScraper/data/cases/seminole/10_7_2022'


def get_onehot_encoded_string(_string, _hash_mod):
    word_indices = []
    for word in _string:
        OneHotWords().put(word)
        word_index = OneHotWords().get(word)
        word_indices.append(word_index)
    # hashed_string = hashlib.sha256(_string.encode('utf-8')).hexdigest(), 16 % 10 ** (8 * _hash_mod)
    print('hash_string: ' + _string)
    # return str(hashed_string[0])
    # base64_bytes = _string.encode("ascii")
    # base64_bytes = base64.b64encode(_string)
    # base64_string = base64_bytes.decode("ascii")
    # return base64_string
    return word_indices


def get_unhashed_string(_hashed_string, _hash_mod):

    # hashed_string = hashlib.sha256(_string.encode('utf-8')).hexdigest(), 16 % 10 ** (8 * _hash_mod)
    # print('hash_string: ' + hashed_string[0])
    # return str(hashed_string[0])
    # sample_string_bytes = _hashed_string.encode("ascii")
    # sample_string_bytes = base64.b64decode(base64_bytes)
    # sample_string = sample_string_bytes.decode("ascii")
    return _hashed_string


def _get_html_escape(_string):
    clean_string = str(_string)
    print("***** test: " + clean_string)
    clean_string = "".join(HTML_ESCAPE_TABLE.get(c, c) for c in clean_string)
    if clean_string.isdigit():
        clean_string = "_" + clean_string
    print('get_html_escape: ' + clean_string)
    return clean_string


def get_clean_key(key):
    clean_key = _get_html_escape(key)
    if clean_key.isdigit():
        clean_key = '_' + clean_key
    return clean_key


class DBTool:
    def __init__(self, _database_name=None, _table_name=None):
        self.base_dir = ROOT_DIR.rsplit('/', 1)[0] + '/'
        # TODO: make table for key storage
        if _database_name is None:
            self.database_name = DB_NAME
        else:
            self.database_name = get_clean_key(_database_name)
        if _table_name is None:
            self.table_name = TABLE_NAME
        else:
            self.table_name = get_clean_key(_table_name)
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
                    result = cursor.fetchone()
            cursor.close()
            connection.close()
        except Error as err:
            if err.errno == 1054 or str(err.args[1]).endswith('exists') or str(err.args[1]).__contains__('Duplicate'):
                print('non-fatal error in DBTool._execute_mysql: ' + _mysql_statement)
            elif err.errno == 1064:
                return 'mysql syntax error: ' +_mysql_statement
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
                    database=get_clean_key(_db_name)
                )
                self.database_name = get_clean_key(_db_name)
            else:
                connection = mysql.connector.connect(
                    host=host_name,
                    user=user_name,
                    passwd=user_password,
                    port=port_num,
                    database=self.database_name
                )
            # print("DBTool._get_db_connection successful: " + db_name)
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
                    mysql_create_database = "CREATE DATABASE {0};".format(get_clean_key(_db_name))
                    cursor.execute(mysql_create_database)
                    connection.commit()
                    self.database_name = get_clean_key(_db_name)
                    # print("_get_db_connection created database: " + db_name)
                except Error as err:
                    print(f"Error: '{err}'")
            else:
                print('_get_db_connection error: ' + _db_name)
                # print('created new database: ' + db_name)
        return connection

    @staticmethod
    def _init_connection():
        connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            passwd=PASSWD,
            port=PORT
        )
        print('_init_user_database: ')
        return connection

    def _get_columns(self):
        connection = self._get_db_connection(HOST, USER, PASSWD, PORT, self.database_name)
        cursor = connection.cursor(buffered=True)
        mysql_statement = "SELECT * FROM {0}".format(self.database_name + '.' + self.table_name)
        cursor.execute(mysql_statement)
        return cursor.description

    def get_row_count(self):
        get_row_count_mysql = "SELECT COUNT(*) FROM " + self.table_name + ";"
        row_count = self._execute_mysql(get_row_count_mysql)
        # print('get_row_count: ' + str(row_count[0]))
        return row_count[0]

    def open_database(self, _database_name, _table_name=None):
        # self.database_name = str(re.sub(LEGAL_CHARACTERS, '_', _database_name.strip()))
        self.database_name = get_clean_key(_database_name)
        if _table_name is not None:
            # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
            self.table_name = get_clean_key(_table_name)

        # When you open_database self.table_name does not change
        # self.table is used in: _add_column, get, get_row_number, open_table, add_dataframe, and put
        # The default value for self.table_name is dbtool
        # Therefore, _table_name may be required for open_database

        # self.database_name = _database_name
        # open_table_mysql = "CREATE TABLE " + self.table_name + "(id int(10) NOT NULL AUTO_INCREMENT," + LINK_KEY + " varchar(255), PRIMARY KEY (id))"
        open_database_mysql = "CREATE DATABASE {0};".format(get_clean_key(_database_name))
        opened_db = self._execute_mysql(open_database_mysql)
        self.open_table(self.table_name)
        print('open_database: ' + _database_name)

    def open_table(self, _table_name):
        # self.table_name = str(re.sub(LEGAL_CHARACTERS, '_', _table_name.strip()))
        self.table_name = get_clean_key(_table_name)
        # clean_table_name = self.get_clean_key(self.table_name)
        mysql_open_table = "CREATE TABLE {0} (id int(10) NOT NULL AUTO_INCREMENT, ".format(self.table_name)
        mysql_open_table += LINK_KEY + " varchar(255), PRIMARY KEY (id));"
        self._execute_mysql(mysql_open_table)
        # self._add_column('link_key')
        # print('open_table: ' + _table_name)

    def _add_column(self, _column_name):
        query = "ALTER TABLE {0} ADD {1} VARCHAR(4096);".format(self.table_name, get_clean_key(_column_name))
        # values = [self.table_name, self.get_clean_key(_column_name)]

        self._execute_mysql(query)
        # print('Add column: '+ _column_name)

    def delete_database(self, _database_name):
        mysql_drop_database = "DROP DATABASE {0}".format(get_clean_key(_database_name))
        self._execute_mysql(mysql_drop_database)
        # print('delete_database: ' + _database_name)

    def delete_table(self, _table_name):
        mysql_drop_table = "DROP DATABASE {0}".format(get_clean_key(_table_name))
        self._execute_mysql(mysql_drop_table)        # print('delete_table: ' + _table_name)

    def get(self, _link_key, _key=None, _value=None):
        if _key is None:
            # 1 result: link_key returns row for link_key
            self._add_column(LINK_KEY)
            sql_statement = SELECT_STATEMENT.format('*', self.table_name, LINK_KEY, get_clean_key(_link_key))
        elif _value is None:
            # 2 result: link_key, value returns the value
            self._add_column(get_clean_key(_link_key))
            sql_statement = SELECT_STATEMENT.format(get_clean_key(_link_key), self.table_name, LINK_KEY, get_clean_key(_link_key))
        else:
            # 3 result: _key, _link_key, _value returns row_number of link_key
            sql_statement = "SELECT {0} FROM {1} WHERE {2} = '{3}';".format(get_clean_key(_key), self.table_name,
                                                                            get_clean_key(_link_key),
                                                                            get_clean_key(_value))
        result = self._execute_mysql(sql_statement)

        return result

    def put(self, _link_key, _key_value=None, _value=None):
        # returns row_number of _link_key
        # 1 value: link_key
        # 2 value: clean_key, value
        # 3 value: link_key, key, value
        result = 'default'
        if _key_value is None:
            row_number = self.get_row_number(_link_key)
            mysql_statement = "SELECT * FROM {0} WHERE {1} = {2};".format(self.table_name, LINK_KEY, get_clean_key(_link_key))
            if row_number == 0:
                # add a link_key = _link_key
                mysql_statement = "INSERT INTO {0} ({1}) VALUES ('{2}');".format(self.table_name, LINK_KEY, get_clean_key(_link_key))
            result = [self.get_row_number(_link_key), _link_key]
            # mysql_statement = "INSERT INTO {0}"
        elif _value is None:
            # copies the value of link_key/_link_key to link_key/_key_value
            row_value = self.get(get_clean_key(_link_key))
            columns = self._get_columns(get_clean_key(_link_key))
            mysql_statement = "UPDATE {0} SET ({1}) = '{2}' WHERE {3} = '{4}';".format(self.table_name, LINK_KEY,
                                                                                       get_clean_key(_link_key),
                                                                                       LINK_KEY,
                                                                                       get_clean_key(_link_key))
            self.put(get_clean_key(_link_key))
            # self._add_column(self.get_clean_key(_key_value))
            row_number = self.get_row_number(get_clean_key(_link_key))
            mysql_statement = "UPDATE {0} SET {1} = '{2}' WHERE id = '{3}';".format(self.table_name, LINK_KEY, get_clean_key(_key_value), row_number)
        else:
            # update set _key_value = _value where id = row_number/link_key
            self.put(get_clean_key(_link_key))
            self._add_column(get_clean_key(_key_value))
            row_number = self.get_row_number(get_clean_key(_link_key))
            mysql_statement = "UPDATE {0} SET {1} = '{2}' WHERE id = '{3}';".format(self.table_name, get_clean_key(_key_value), get_clean_key(_value), row_number)
        self._execute_mysql(mysql_statement)
        # print('put: ')
        result = self.get_row_number(get_clean_key(_link_key))
        return result

    def get_row_number(self, _link_key, _key=None):
        # select_template = '''SELECT * FROM seminole_main.seminole_main where link_key = "jurney";'''
        # clean_link_key = str(re.sub(LEGAL_CHARACTERS, '_', clean_link_key.strip()))
        clean_link_key = get_clean_key(_link_key)
        if _key is None:
            select_sql = "SELECT id FROM {0} WHERE {1} = '{2}';".format(self.table_name, LINK_KEY, clean_link_key)
        else:
            clean_key = get_clean_key(_key)
            select_sql = "SELECT id FROM {0} WHERE {1} = '{2}';".format(self.table_name, LINK_KEY, clean_key)

        row_number = self._execute_mysql(select_sql)
        # print('get_row_number: ' + clean_link_key + ' = ' + str(row_number))
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
                self.put(get_clean_key(link_key), get_clean_key(key), get_clean_key(value))
        # print('add_dataframe done!')

    def get_column_based_name(self, _dataframe):
        columns = _dataframe.columns.values
        columns = columns.tolist()
        column_based_name = ''
        for column in columns:
            this_column = get_clean_key(column)
            column_based_name += this_column
        print('get_column_based_name: ')
        return column_based_name


class Pkl2Sql(DBTool):
    def __init__(self, _db_name, _dir_path):
        super().__init__(_db_name)
        self.dir_path = self.base_dir + get_clean_key(_dir_path)
        self.table_names = self._add_pickles()
        self.unencoded_table_names = self._get_unencoded_table_names()
        # print('Pickle2MySQL.__init__ done!')

    def get_all_column_names(self):
        # this returns the unhashed column_names that were added by _add_pickles
        print('get_all_column_names done!')
        return self.column_names

    def _add_pickles(self):
        files = self.get_files(self.dir_path, '.pkl')
        hashed_column_names = []
        for file in files:
            this_pickle = pandas.read_pickle(file)
            columns = this_pickle.columns
            columns = map(str, columns)
            joined_columns = '-'.join(columns)
            these_columns = get_onehot_encoded_string(this_pickle.columns, HASH_MOD)
            if not hashed_column_names.__contains__(these_columns):
                hashed_column_names.append(these_columns)
            dbtool = DBTool(self.database_name, these_columns)
            dbtool.add_dataframe(this_pickle, 0)
        # print('add_pickles done!')
        return hashed_column_names

    @staticmethod
    def get_files(_base_directory, _extension):
        selected_files = []
        for root, dirs, files in os.walk(_base_directory):
            for file in files:
                if file.endswith(_extension):
                    selected_files.append(os.path.join(root, file))
                    # print(os.path.join(root, file))
        # print('get_files done!')
        return selected_files

    def _get_unencoded_table_names(self):
        unencoded_table_names = []
        for table_name in self.table_names:
            this_unencoded_table_name = get_unhashed_string(table_name, 1)
            unencoded_table_names.append(this_unencoded_table_name)
        print('get_unencoded_table_names done!')
        return unencoded_table_names


class Sql2Pkl(DBTool):
    # DB2Pkl takes a database_name and table_name and returns a pandas.DataFrame
    def __init__(self, _database_name, _table_name):
        super().__init__(_database_name, _table_name)
        print('DB2Pkl.__init__ done!')

    def get_dataframe(self):
        print('get_dataframe done!')


class OneHotWords(DBTool):
    # mysql has a maximum number of 4096 columns per table
    # Therefore, each sentence has a maximum number of words
    def __init__(self):
        super().__init__(ONEHOT_DB_NAME, ONE_HOT_WORD_TABLE_NAME)
        # print('__init__ done!')

    def get_index_combo(self, _string):
        words = self.get_clean_string(_string)
        words = words.split(' ')
        word_indicies = []
        for word in words:
            word_indicies.append(self.get_row_number(word))
        index_combo = ''
        first = True
        for word_index in word_indicies:
            if not first:
                index_combo += '&'
            else:
                first = False
            index_combo += str(word_index)
        return index_combo

    def get_reconstituted_string(self, _index_combo):
        indices = _index_combo.split('&')
        words = []
        for index in indices:
            this_word = self.get_word_at_index(index)
            if this_word is not None:
                words.append(this_word)
        reconstituted_string = ''
        first = True
        for word in words:
            if not first:
                reconstituted_string += ' '
            else:
                first = False
            # # print('get_reconstituted_string word: ' + word)
            reconstituted_string += str(word[0])
        return reconstituted_string

    def get_word_at_index(self, _index):
        sql_statement = "SELECT link_key FROM {0} WHERE id = '{1}';".format(self.table_name, str(_index))
        this_word = self._execute_mysql(sql_statement)
        # print('get_word_at_index done!')
        return this_word

    def _put_word(self, _word, _word2=None, _word3=None):
        clean_word = get_clean_key(_word)
        super().put(LINK_KEY, clean_word)
        # print('onehottool.put: ' + clean_word)

    def _get_index(self, _word):
        # This function returns the row number of _word in the onehot index
        clean_word = self.get_clean_string(_word)
        row_number = super().get_row_number(clean_word)
        if row_number == '0':
            self.put_word(clean_word)
            row_number = super().get_row_number(clean_word)
        # print('onehottool.get: ' + str(row_number))
        return row_number

    def load_dict(self, _dict_table_name, _dict_file_path):
        self.open_table(_dict_table_name)
        file_path = _dict_file_path
        file = open(file_path, 'r')
        text = file.read()
        words = text.split('\n')
        for word in words:
            if word == 'ain''t':
                clean_word = 'xyxxy'
            clean_word = get_clean_key(word)
            self._put_word(clean_word)


def test_init():
    dbtool = DBTool()
    # print('test_init done!')


def test_put():
    dbtool = DBTool()
    # make link_key/word_1
    # dbtool.put('word')
    # dbtool.put('put_1')
    dbtool.put('xyzzy', 'failures', '543')
    # dbtool.put('put_2')
    # dbtool.put('put_2', 'failures', '345')
    # dbtool.put('put_1', 'xyzzy')

    # dbtool.put('old_index_1', "old_index_2")
    # if link_key/word_1 does not exist then creates link_key/word_1 and renames link_key to word_1a
    # if link_key for word_1 does exist then this changes link_key/word_1 to word_1a
    # dbtool.put('word_1', 'word_1a')
    # sets key/word_1 to value/word_1a in row with link_key/word_1b
    # dbtool.put('word_1', 'word_1a', 'word_1b')
    # print('test_put done!')


def test_get():
    dbtool = DBTool()
    link_key_index = dbtool.get('put_2')
    print('index of put_2 from test_get(): ' + str(link_key_index))
    # link_key_update_status = dbtool.get('put_1', 'reput_1')
    # print(link_key_update_status)


def test_get_row_count():
    dbtool = DBTool('dbtool', 'dbtool')
    row_count = dbtool.get_row_count()
    print('test_get_row_count: ' + str(row_count))


def test_get_clean_key():
    KEY = "Instrument #"
    dbtool = DBTool()
    clean_key = get_clean_key(KEY)
    print('test_get_clean_key: ' + clean_key)


def test_add_data_frame():
    # create the test data_frame
    data = [['bilbo', 'baggins'], ['thoron', 'falbright']]
    data_frame = pandas.DataFrame(data)
    data_frame = data_frame.transpose()
    columns = ['username', 'password']
    data_frame.columns = columns
    # test the system
    dbtool = DBTool()
    column_based_name = dbtool.get_column_based_name(data_frame)
    dbtool.add_dataframe(data_frame)
    print('test_add_dataframe: ')


def test_pkl2sql():
    # create the test data_frame and pickle file
    data = [['bilbo', 'baggins'], ['thoron', 'falbright']]
    data_frame = pandas.DataFrame(data)
    data_frame = data_frame.transpose()
    columns = ['username', 'password']
    data_frame.columns = columns
    output_file_path = '../data/users.pkl'
    data_frame.to_pickle(output_file_path)
    # test the system
    pkl2sql = Pkl2Sql(DB_NAME, 'data/')
    print('test_pkl2sql done!')


def test_sql2pkl():
    # this class creates a pandas DataFrame
    sql2pkl = Sql2Pkl(DB_NAME, TABLE_NAME)
    dataframe = sql2pkl.get_dataframe()

    print('test_sql2pkl done!')


if __name__ == '__main__':
    # test_init()
    test_put()
    # test_get()
    # test_get_row_count()
    # test_add_data_frame()
    # test_get()
    # test_get_clean_key()
    # test_pkl2sql()
    # test_sql2pkl()
    # the following line is not reached because of sys.exit() in main()
    print("dbtool done!")
