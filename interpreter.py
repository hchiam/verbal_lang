from sys import *
from importlib import import_module
import importlib.util


# functions:

def interpret():
    text = open_file(argv[1]) # so you can use this Terminal command: python interpreter.py text.txt
    text = text.lower() # lowercase
    sentences = get_sentences(text)
    # print('  DEBUG OUTPUT: ' + sentences)
    words_grouped = get_words_grouped_by_sentence(sentences)
    # print('  DEBUG OUTPUT: ' + words_grouped)
    run_commands(words_grouped)

def open_file(file_name):
    text = open(file_name, 'r').read()
    return text

def get_sentences(text):
    sentences = text.split('please') # each sentence is expected to begin with "please"
    return sentences

def get_words_grouped_by_sentence(sentences):
    word_groups = [] # instead of "= sentences", which would pass by reference
    for sentence in sentences:
        words = list(sentence.strip().split()) # no params for split so it uses any whitespace character
        word_groups.append(words)
    return word_groups

def run_commands(words_grouped):
    for sentence in words_grouped:
        # print('  DEBUG OUTPUT: ' + 'sentence = ' + str(sentence))
        words_count = len(sentence)
        for i, word in enumerate(sentence): # need to track number of words left in sentence while read each word
            words_left = words_count - i
            sentence_data = sentence_info(word, words_left)
            check_print(sentence_data)
            check_spell(sentence_data)
            if print_state == False:
                check_math(sentence_data)
                check_import(sentence_data)
                check_use(sentence_data)

"""
example:
please print this string of words
"""
def check_print(sentence_data):
    global print_state
    global print_string
    word = sentence_data.word
    words_left = sentence_data.words_left
    if print_state == False and word == 'print':
        print_state = True
    elif print_state == True:
        if words_left > 1:
            print_string += ' ' + word
        elif words_left == 1:
            print_string += ' ' + word
            print_string = print_string.strip() # .strip() removes leading and trailing spaces
            print(print_string)
            # reset variables
            print_state = False
            print_string = ''

"""
example:
please one plus two
"""
def check_math(sentence_data):
    global math_state
    global math_string
    word = sentence_data.word
    words_left = sentence_data.words_left
    word_uses_math_keyword = (word in math_words_numbers or word in math_words_operators)
    if math_state == False and word_uses_math_keyword:
        math_state = True
        math_string = word
    elif math_state == True:
        if words_left > 1 and word_uses_math_keyword:
            math_string += ' ' + word
        elif words_left > 1 and not word_uses_math_keyword:
            math_string = math_string.strip()
            evaluated_expression = eval_math(translate_math(math_string))
            print('  DEBUG MATH: ' + str(evaluated_expression))
            # reset variables
            math_state = False
            math_string = ''
        elif words_left == 1:
            if word_uses_math_keyword:
                math_string += ' ' + word
            math_string = math_string.strip()
            evaluated_expression = eval_math(translate_math(math_string))
            print('  DEBUG MATH: ' + str(evaluated_expression))
            # reset variables
            math_state = False
            math_string = ''

def translate_math(expression_string):
    global math_words_numbers
    output_string = ''
    expression = expression_string.split()
    for word in expression:
        if word in math_words_numbers:
            output_string += str(math_words_numbers[word])
        elif word in math_words_operators:
            output_string += str(math_words_operators[word])
    return output_string

def eval_math(expression):
    return eval(expression,{"__builtins__":None},{}) # use ,{"__builtins__":None},{} to make eval function safer

"""
example:
please spell with the first letters of Neptune unicorn moose panda Yoda
"""
def check_spell(sentence_data):
    global spell_state
    global spell_string
    global spell_phrase_index
    global spell_checkphrase
    word = sentence_data.word
    words_left = sentence_data.words_left
    if spell_state == False:
        checkword = spell_checkphrase[spell_phrase_index]
        if word == checkword:
            if spell_phrase_index == len(spell_checkphrase)-1:
                spell_state = True
            else:
                spell_phrase_index += 1
        else:
            spell_phrase_index = 0
    elif spell_state == True:
        spell_string += ' ' + word
        if words_left == 1:
            spell_string = spell_with_first_letters(spell_string)
            print('  DEBUG SPELL: ' + spell_string)
            # reset variables
            spell_state = False
            spell_string = ''
            spell_phrase_index = 0

def spell_with_first_letters(sentence):
    spelt_word = ''
    words = sentence.split()
    spelt_word = ''.join(list(word[0] for word in words))
    return spelt_word

"""
example:
please import test
please import numpy as nectarine pony
"""
def check_import(sentence_data):
    global import_state
    global import_string
    global import_dictionary
    global as_state
    global as_string
    global spell_state
    global from_state
    global from_string
    word = sentence_data.word
    words_left = sentence_data.words_left
    if import_state == False and word == 'import':
        import_state = True
    elif import_state == True:
        if words_left > 1 and word != 'as' and word != 'from':
            if as_state == False and from_state == False:
                import_string += ' ' + word
            elif as_state == True:
                as_string += ' ' + word
            elif from_state == True:
                from_string += ' ' + word
        elif words_left > 1 and word == 'as' and as_state == False:
            as_state = True
            spell_state = True # to use check_spell()
        elif words_left > 1 and word == 'from' and from_state == False:
            from_state = True
        elif words_left == 1:
            dictionary_key = import_string
            if as_state == False and from_state == False:
                import_string += ' ' + word
                dictionary_key = import_string
            elif as_state == True:
                as_string += ' ' + word
                dictionary_key = spell_with_first_letters(as_string)
            elif from_state == True:
                from_string += ' ' + word
                #from_string = spell_with_first_letters(from_string)
                dictionary_key = import_string
            import_string = import_string.strip()
            dictionary_key = dictionary_key.strip()
            from_string = from_string.strip()
            print('  DEBUG IMPORT: import_string = ' + import_string)
            print('  DEBUG IMPORT: dictionary_key = ' + dictionary_key)
            if from_state == True:
                # importing from folder
                print('  DEBUG IMPORT: from_string = ' + from_string)
                # http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
                spec = importlib.util.spec_from_file_location(import_string, from_string + '/' + import_string + '.py')
                module = importlib.util.module_from_spec(spec) # get module
                spec.loader.exec_module(module) # enables use of functions and variables from the module
            elif from_state == False:
                module = import_module(import_string)
            import_dictionary[dictionary_key] = module
            print('  DEBUG IMPORT: ' + str(import_dictionary))
            # reset variables
            import_state = False
            import_string = ''
            as_state = False
            as_string = ''
            spell_state = False
            from_state = False
            from_string = ''

"""
example:
please import test
please use test_function of test
please use test_function from test
"""
def check_use(sentence_data):
    global use_state
    global use_string
    global from_state
    global from_string
    word = sentence_data.word
    words_left = sentence_data.words_left
    if use_state == False and word == 'use':
        use_state = True
    elif use_state == True:
        if words_left > 1 and (word != 'of' and word != 'from') and from_state == False:
            use_string += ' ' + word
            # print('use_string ' + use_string)
        elif words_left > 1 and (word == 'of' or word == 'from'):
            from_state = True
            # print('from_state = True')
        elif words_left > 1 and from_state == True:
            from_string += ' ' + word
            from_string = from_string.strip()
            # print('from_string = ' + from_string)
        elif words_left == 1:
            if from_state == True:
                from_string += ' ' + word
                from_string = from_string.strip()
                # print('from_string = ' + from_string)
            use_string = use_string.strip()
            print('  DEBUG USE: ' + use_string)
            # print('from_string = ' + from_string)
            function_imported = getattr(import_dictionary[from_string], use_string)
            try:
                function_imported() # try to use function_imported as a function
            except:
                print(function_imported) # in case function_imported is just an output value
            # reset variables
            use_state = False
            use_string = ''
            from_state = False
            from_string = ''


# initialize global variables:
print_state = False
print_string = ''
math_state = False
math_string = ''
math_result = ''
math_words_numbers = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,
                      'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,
                      'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19,
                      'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,'eighty':80,'ninety':90,
                      'hundred':'00','thousand':'000','million':'000000','billion':'000000000','trillion':'000000000',
                      '0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9}
math_words_operators = {'plus':'+','minus':'-','times':'*','divide':'/'}
spell_state = False
spell_string = ''
spell_phrase_index = 0
spell_checkphrase = ['spell','with','the','first','letters','of']
import_state = False
import_string = ''
import_dictionary = {}
as_state = False
as_string = ''
use_state = False
use_string = ''
from_state = False
from_string = ''
class sentence_info():
    word = ''
    words_left = 0
    def __init__(self, word, words_left):
        self.word = word
        self.words_left = words_left


# run this interpreter:
interpret()
