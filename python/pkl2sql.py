import os

import pandas

from python.dbtool import DBTool, get_clean_key, get_onehot_encoded_string, HASH_MOD

DEFAULT_PKL_PATH = '../data/users.pkl'


def get_files(_base_directory, _extension):
    selected_files = []
    for root, dirs, files in os.walk(_base_directory):
        for file in files:
            if file.endswith(_extension):
                selected_files.append(os.path.join(root, file))
    # print('get_files done!')
    return selected_files


class Pkl2Sql(DBTool):
    def __init__(self, _db_name, _dir_path):
        # This class gets .pkl files and puts them into mysql
        # A mysql database is created with the name _db_name
        # All .pkl files in subdirectories starting with _dir_path are gathered
        # _db_name is where the various tables will be stored
        super().__init__(_db_name)
        self.dir_path = self.base_dir + get_clean_key(_dir_path)
        self.table_names = self._add_pickles()
        # print('Pickle2MySQL.__init__ done!')

    def _add_pickles(self):
        files = get_files(self.dir_path, '.pkl')
        hashed_column_names = []
        for file in files:
            this_pickle = pandas.read_pickle(file)
            these_columns = get_onehot_encoded_string(this_pickle.columns, HASH_MOD)
            if not hashed_column_names.__contains__(these_columns):
                hashed_column_names.append(these_columns)
            dbtool = DBTool(self.database_name, these_columns)
            dbtool.add_dataframe(this_pickle, 0)
        # print('add_pickles done!')
        return hashed_column_names


def create_simple_pkl():
    # create the test data_frame and pickle file
    user_data = [['bilbo', 'thoron'], ['baggins', 'falbright']]
    data_frame = pandas.DataFrame(user_data)
    columns = ['username', 'password']
    data_frame.columns = columns
    data_frame.to_pickle(DEFAULT_PKL_PATH)


def test_pkl2sql():
    # test the system
    pkl2sql = Pkl2Sql('pkl2sql', 'data/')

    print('test_pkl2sql database_name: ' + pkl2sql.database_name)


if __name__ == '__main__':
    create_simple_pkl()
    test_pkl2sql()
