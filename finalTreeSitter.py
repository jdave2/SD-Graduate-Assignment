import re
from tree_sitter import Language, Parser
import os
from git import Repo
from fnmatch import fnmatch
import keyword
import builtins
import types
from javascript_builtin import built_in_js, keywords_js
from go_builtin import builtins_go, keyword_go
from ruby_builtin import keyword_rb, builtins_ruby
import nltk
from nltk.corpus import words

def initTreeSitter(selectLang):
    Language.build_library(
        'build/my-languages.so',
        [
            './tree-sitter-go',
            './tree-sitter-javascript',
            './tree-sitter-python',
            './tree-sitter-ruby',
        ]
    )
    language_go = Language('build/my-languages.so', 'go')
    language_js = Language('build/my-languages.so', 'javascript')
    language_py = Language('build/my-languages.so', 'python')
    language_rb = Language('build/my-languages.so', 'ruby')

    parser = Parser()
    language = ''
    if selectLang == 'python':
        parser.set_language(language_py)
        language = language_py
    if selectLang == 'javascript':
        parser.set_language(language_js)
        language = language_js
    if selectLang == 'go':
        parser.set_language(language_go)
        language = language_go
    if selectLang == 'ruby':
        parser.set_language(language_rb)
        language = language_rb

    return parser, language

def readFiles(codeLang, gitUrl):
    try:
        Repo.clone_from(gitUrl, 'cloneRepo/')
    except:
        pass

    file_list = []
    root = os.getcwd() + '/cloneRepo'
    if codeLang == 'python':
        pattern = "*.py"
    if codeLang == 'javascript':
        pattern = "*.js"
    if codeLang == 'go':
        pattern = "*.go"
    if codeLang == 'ruby':
        pattern = "*.rb"

    for path, _, files in os.walk(root):
        for file in files:
            if fnmatch(file, pattern):
                a = 'cloneRepo' + (path + '/' + file).split('cloneRepo')[1]
                file_list.append(a)
    for file in file_list:
        with open(file) as f:
            lines = f.read()
    exp = bytes(lines, 'utf-8')
    return exp
def findIdQuery(codeLang, tree, exp, query, outUrl, out2Url):
    shortIdList = ['c','d','e','g','i','in','inOut','j','k', 'm', 'n', 'o', 'out', 't', 'x', 'y', 'z']
    word_list = words.words()
    keywords_py = keyword.kwlist
    builtin_py = [name for name, obj in vars(builtins).items()
                              if isinstance(obj, types.BuiltinFunctionType)]
    if codeLang == 'python':
        keywords = keywords_py
        builtin_function_names = builtin_py
    if codeLang == 'javascript':
        keywords = keywords_js
        builtin_function_names = built_in_js
    if codeLang == 'go':
        keywords = keyword_go
        builtin_function_names = builtins_go
    if codeLang == 'ruby':
        keywords = keyword_rb
        builtin_function_names = builtins_ruby

    captures = query.captures(tree.root_node)
    idList = {}
    type_list_python = ('str', 's', 'int', 'i', 'float', 'f', 'complex', 'list', 'lst', 'tuple', 'range',
                        'dict', 'set', 'frozenset', 'bool', 'bytes', 'bytearray', 'b')

    numeric_list = ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'
                    , 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
                    'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty', 'thirty', 'fourty', 'fifty', 'sixty')
    for i in captures:
        name = exp[i[0].start_byte:i[0].end_byte].decode('utf8')
        if name not in idList.keys():
            idList[name] = []

    for name, value in idList.items():
        if (name not in keywords) and (name not in builtin_function_names):

            res_list_cap = re.findall('[A-Z]*[^A-Z]*', name)
            res_list_unders = name.split('_')
            if (len(name) > 12):
                idList[name].append("Long Identifier")

            if (len(name) < 4 and name not in shortIdList):
                idList[name].append("Short Identifier")

            if (re.search(r'^[a-zA-Z]+_+$', name) or re.search(r'^_+[a-zA-Z]+_*$', name)):
                idList[name].append("External Underscore")

            if (re.search(r'^[a-z0-9_]*[A-Z]{2,}[a-z0-9_]*', name)):
                idList[name].append("Naming Convention Anomaly")

            if (len(name)<3 and re.search(r'^[a-z0-9_]*[A-Z]{2,}[a-z0-9_]*', name) or re.search(r'^[a-z]*$', name)):
                idList[name].append("Capitalization Anomaly")

            if (re.search(r'^[a-zA-Z0-9]*_{2,}[a-zA-Z0-9]*$', name)):
                idList[name].append("Multiple Underscore")

            if (len(res_list_cap) > 4 or len(res_list_unders) > 4):
                idList[name].append("More Than 4 Words")

            if(name.find('_') != -1):
                for word in res_list_unders:
                    if (word not in word_list and len(word) > 2):
                        idList[name].append("Dictionary Error")
                        break
            if (name.find('_') == -1):
                # pass
                for word in res_list_cap:
                    word = word.lower()
                    if (word not in word_list and len(word)>2 and word!=''):
                        idList[name].append("Dictionary Error")
                        break

            if (res_list_cap[0] in type_list_python or res_list_unders[0] in type_list_python):
                idList[name].append("Identifier Encoding")

            count = 0
            for word in res_list_cap:
                word = word.lower()
                if word in numeric_list:
                    count = count + 1
                else:
                    pass
            for word in res_list_unders:
                word = word.lower()
                if word in numeric_list:
                    count = count + 1
                else:
                    pass
            if (name.find('_') != -1):
                if (count == len(res_list_unders) and len(res_list_unders) > 0):
                    idList[name].append("Numeric Identifier Name")
            if (name.find('_') == -1):
                if (count == len(res_list_cap) and len(res_list_cap) > 0):
                    idList[name].append("Numeric Identifier Name")
    saveFile(idList, keywords, builtin_function_names, outUrl, out2Url)

def saveFile(idList,keywords,builtin_function_names,outUrl,out2Url):
    os.chdir(outUrl)
    with open('output1.txt', 'w') as f1:
        keywords = [each_string.lower() for each_string in keywords]
        builtin_function_names = [each_string.lower() for each_string in builtin_function_names]
        for key in idList:
            if (len(idList[key]) == 0 and key.lower() not in keywords and key.lower() not in builtin_function_names):
                string = 'Identifier Name:' + str(key) + '\n'
                f1.write(string)
    os.chdir(out2Url)#C:\Users\JD\Downloads\SDOut
    with open("output2.txt", 'w') as f2:
        keywords = [each_string.lower() for each_string in keywords]
        builtin_function_names = [each_string.lower() for each_string in builtin_function_names]
        for key in idList:
            if (len(idList[key]) > 0 and key.lower() not in keywords and key.lower() not in builtin_function_names):
                string = '\n' + 'Identifier Name: ' + str(key) + '\n'
                error = ''
                for i in idList[key]:
                    error = error + ', ' + str(i)
                f2.write(string)
                f2.write(error)
                f2.write('\n')

def main():
    codeLang = input("Enter Language")
    gitUrl = input("Enter git URL")
    outUrl = input("Enter Output 1 Location")
    outUrl2 = input("Enter Output 2 Location")
    parser,language = initTreeSitter(codeLang)
    expression = readFiles(codeLang, gitUrl)#'https://github.com/jdave2/projectHW'
    tree = parser.parse(expression)
    query = language.query("""
            ((identifier) @constant)
            """)
    findIdQuery(codeLang, tree, expression, query, outUrl, outUrl2)
if __name__ == "__main__":
    main()