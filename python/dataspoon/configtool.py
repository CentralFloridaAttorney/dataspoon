from configparser import ConfigParser

DEFAULT_INI_FILE_PATH = '../../data/ini/configtool_default.ini'
DEFAULT_INI = {
            "user": "bilbo",
            "passwd": "baggins",
            "port": "(3306/50011)",
            "host": "(localhost/192.168.1.227)",
            "database_name": "dbtool_db",
            "table_name": "dbtool_table"
        }


class ConfigTool:
    def __init__(self, _config_key):
        self.config_key = _config_key
        print('__init__ done!')

    def write_default_configs(self):
        file_path = '../../data/ini/' + self.config_key + '.ini'
        #Get the configparser object
        config_object = ConfigParser()
        #Assume we need 2 sections in the config file, let's call them USERINFO and SERVERCONFIG
        config_object["DEFAULT"] = DEFAULT_INI
        config_object["DEFAULT"]["user"] = self.config_key
        config_object["DEFAULT"]["INI_FILE_PATH"] = file_path
        #Write the above sections to config.ini file
        with open(file_path, 'w') as conf:
            config_object.write(conf)

    def get_configs(self):
        file_path = '../../data/ini/' + self.config_key + '.ini'
        config_object = ConfigParser()
        config_object.read(file_path)
        sections = config_object.sections()
        config_list = []
        for section in sections:
            config_values = [section, config_object.items(section)]
            config_list.append(config_values)
        return config_list


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