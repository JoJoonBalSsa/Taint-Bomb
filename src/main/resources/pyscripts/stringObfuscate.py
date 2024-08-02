from stringSearch import stringSearch
from stringEncrypt import stringEncrypt
from stringInsert import stringInsert

from obfuscateTool import obfuscateTool

class stringObfuscate :
    def __init__(self, output_folder) :
        search_str = stringSearch(output_folder)
        random_classes = obfuscateTool.random_class(search_str.class_names, 2)

        encrypt_str = stringEncrypt(search_str.Literals)

        insert_str = stringInsert(search_str.Literals,encrypt_str.encrypted_Literals,random_classes,output_folder)