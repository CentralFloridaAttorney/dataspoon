import configparser


FIELD_1 = 'INI_FILE_PATH'
FIELD_2 = 'HOST'
FIELD_3 = 'port'
FIELD_4 = 'USER'
FIELD_5 = 'PASSWD'
FIELD_6 = ''
FIELD_7 = ''
FIELD_8 = ''


class DBToolConfigs:
    def __init__(self, _config_key):
        # _config_key is the file_name part of the .ini file
        file_path = '../../data/ini/' + _config_key + '.ini'
        self._config_write(file_path)
        self.configs = self.load_configs(file_path)

    @staticmethod
    def load_configs(_file_path):
        # Read config.ini file
        config_object = configparser.ConfigParser()
        config_object.read(_file_path)

        # Get the password
        userinfo = config_object["DBTOOL"]
        print("Port is {}".format(userinfo["port"]))
        return userinfo

    @staticmethod
    def _config_write(_file_path):
        config = configparser.ConfigParser()
        # config.read(_file_path)
        config["DBTOOL"][FIELD_1] = _file_path
        config["DBTOOL"][FIELD_2] = 'localhost'
        config["DBTOOL"][FIELD_3] = '3306'  # create
        config["DBTOOL"][FIELD_4] = 'bilbo'  # create
        config["DBTOOL"][FIELD_5] = 'baggins'  # create
        # create
        with open(_file_path, 'w') as configfile:  # save
            config.write(configfile)
        print('_config_write done!')


def test_init():
    configtool = DBToolConfigs('dbtool_bilbo')
    print('test_init done!')


if __name__ == '__main__':
    test_init()
    print("dbtoolconfigs.py.__main__ done!")