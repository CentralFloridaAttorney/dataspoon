import re

LEGAL_CHARACTERS = r"[^'a-zA-Z0-9\s\·\,\.\:\:\(\)\[\]\\\\]]"
ILLEGAL_WORDS = ['True']
HTML_ESCAPE_TABLE = {
    '"': "_&quot;",
    "'": "_&apos;",
    "\n": "_&#013",
    "True": "_1",
    "False": "_0",
    "‘": "_&#x2018;",
    "’": "_&#x2019;",
    "(": "_&#x28;",
    ")": "_&#x29;",
    "”": "_&#x201d;",
    "<": "_&#x3c;",
    ">": "_&#x3c;"
}
WORD_BREAK_CHARACTERS = "[ . | ' ' | , | :]"
HTML_UNESCAPE_TABLE = {
    "_&#x27;": "'",
    "_&quot;": "\""
}


class TextProcessor:
    def __init__(self, _given_string="that's given!", _output_path='../../data/textprocessor.txt'):
        self.given_string = _given_string
        self.output_path = _output_path

    def save_processed_string(self):
        processed_string = self.get_processed_string(self.given_string)
        text_file = open(self.output_path, 'w+')
        text_file.write(processed_string)
        text_file.close()

    def load_given_string(self, _file_path):
        text_file = open(_file_path, 'r+')
        self.given_string = text_file.read()
        text_file.close()

    def get_processed_string(self, _string=None):
        if _string is None:
            _string = self.given_string
        clean_string = self.get_replaced_characters(_string)
        split_words = re.split(WORD_BREAK_CHARACTERS, clean_string)
        clean_split_words = list(filter(None, split_words))
        processed_string = ""
        for word in clean_split_words:
            processed_string = processed_string + "," + word
        processed_string = processed_string.rstrip(',')
        return processed_string

    @staticmethod
    def get_replaced_characters(_string):
        for item in HTML_ESCAPE_TABLE:
            _string = _string.replace(item, HTML_ESCAPE_TABLE.get(item))
        return _string

    def get_clean_word(self, _string):
        """
        :param _string: the string to be processed
        :return:
        """
        clean_string = self.get_replaced_characters(_string)
        return clean_string


def test_init():
    textprocessor = TextProcessor()
    textprocessor.load_given_string('../../data/txt/shakespear.txt')
    textprocessor.save_processed_string()


if __name__ == '__main__':
    test_init()
