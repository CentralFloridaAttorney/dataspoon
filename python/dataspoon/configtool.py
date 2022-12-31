from configparser import ConfigParser

DEFAULT_INI_FILE_PATH = '../../data/ini/configtool_default.ini'
DEFAULT_INI = {
            "ini_file_path": "../../default.ini",
            "user": "bilbo",
            "passwd": "baggins",
            "port": "3306",
            "host": "localhost",
            "database_name": "dbtool_db",
            "table_name": "dbtool_table",
            "onehotdb_name": "onehotwords",
            "onehotdb_table": "words",
            "words_filename_key": "default_words"
        }


class ConfigTool:
    def __init__(self, _config_key):
        self.config_key = _config_key
        print('__init__ done!')

    def write_default_configs(self):
        file_path = '../../' + self.config_key + '.ini'
        #Get the configparser object
        config_object = ConfigParser()
        #Assume we need 2 sections in the config file, let's call them USERINFO and SERVERCONFIG
        config_object["DEFAULT"]["user"] = self.config_key
        config_object["DEFAULT"]["INI_FILE_PATH"] = file_path
        config_object["DEFAULT"] = DEFAULT_INI

        #Write the above sections to config.ini file
        with open(file_path, 'w') as conf:
            config_object.write(conf)

    def get_configs(self):
        file_path = '../../' + self.config_key + '.ini'
        config_object = ConfigParser()
        config_object.read(file_path)
        return config_object.defaults()


def test_init(_user):
    config_demo = ConfigTool(_user)
    print('test_init done!')


def test_write_default_configs(_user):
    configtool = ConfigTool(_user)
    configtool.write_default_configs()


def test_get_configs(_user):
    configtool = ConfigTool(_user)
    configs = configtool.get_configs()
    print('test_get_default_configs done!')


def test_get_values(_user):
    configtool = ConfigTool(_user)
    values = configtool.get_configs()
    print('get_values done!')


if __name__ == '__main__':
    _user = 'default'
    test_init(_user)
    test_write_default_configs(_user)
    test_get_configs(_user)
    test_get_values(_user)
    print("config_demo done!")
