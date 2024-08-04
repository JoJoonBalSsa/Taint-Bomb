from stringSearch import stringSearch
from stringEncrypt import stringEncrypt
from stringInsert import stringInsert

from obfuscateTool import obfuscateTool


class StringObfuscate:
    def __init__(self, output_folder, keyDecryptJava, stringDecryptJava):
        searched_strings = stringSearch(output_folder)

        encrypted_strings = stringEncrypt(searched_strings.Literals)

        random_classes = obfuscateTool.random_class(searched_strings.class_names, 2)
        stringInsert(searched_strings.Literals, encrypted_strings.encrypted_Literals, random_classes, output_folder,
                     keyDecryptJava, stringDecryptJava)
