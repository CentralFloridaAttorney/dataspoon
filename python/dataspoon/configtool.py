from configparser import ConfigParser
from configparser import ConfigParser

DEFAULT_INI_FILE_PATH = '../../data/ini/configtool_default.ini'


class ConfigTool:
    def __init__(self):
        # self.write_default_configs()
        print('__init__ done!')

    @staticmethod
    def write_default_configs(_config_key):
        file_path = '../../data/ini/' + _config_key + '.ini'
        #Get the configparser object
        config_object = ConfigParser()

        #Assume we need 2 sections in the config file, let's call them USERINFO and SERVERCONFIG
        config_object["USERINFO"] = {
            "user": "bilbo",
            "passwd": "baggins"
        }

        config_object["MYSQL"] = {
            "port": "3306",
            "host": "localhost",
            "database_name": "dbtool_db",
            "table_name": "dbtool_table"
        }

        #Write the above sections to config.ini file
        with open(file_path, 'w') as conf:
            config_object.write(conf)

    @staticmethod
    def get_default_configs():
        config_object = ConfigParser()
        config_object.read(DEFAULT_INI_FILE_PATH)
        return config_object


def test_init():
    config_demo = ConfigTool()
    print('test_init done!')


def test_write_default_configs():
    configtool = ConfigTool()
    configtool.write_default_configs('overlordx')


if __name__ == '__main__':
    test_init()
    print("config_demo done!")
