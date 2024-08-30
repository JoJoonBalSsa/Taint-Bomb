from stringSearch import StringSearch
from stringEncrypt import StringEncrypt
from stringInsert import StringInsert

from obfuscateTool import ObfuscateTool


class StringObfuscate:
    def __init__(self, output_folder, keyDecryptJava, stringDecryptJava):
        searched_strings = StringSearch(output_folder)
        print("string search complete")

        encrypted_strings = StringEncrypt(searched_strings.Literals)
        print("string encrypt complete")
        
        random_classes = ObfuscateTool.random_class(searched_strings.class_names, 2)
        StringInsert(searched_strings.Literals, encrypted_strings.encrypted_Literals, random_classes, output_folder,
                     keyDecryptJava, stringDecryptJava)
        print("string insert complete")