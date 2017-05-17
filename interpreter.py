# interpret() function is where you should start reading to understand this code.
# interpret() has to be called at the bottom of this file for things to work.

from sys import *
import re
from importlib import import_module
import importlib.util
import copy



# functions:

def interpret():
    file_name = argv[1] # so you can use this Terminal command: python interpreter.py text.txt
    text = get_text(file_name)
    text = text.lower() # lowercase
    text = remove_multi_spaces(text)
    sentences = get_sentences(text)
    setup_goto_locations_and_functions(sentences)
    run_commands(sentences)

def get_text(file_name):
    text = open(file_name, 'r').read() # for example: file_name = "text.txt"
    return text

def remove_multi_spaces(text):
    return ' '.join(text.split())

def get_sentences(text):
    # each sentence is expected to begin with "please "
    sentences = text.split('please ')[1:] # assume index [0] is always empty or invalid before the first "please "
    return sentences

def setup_goto_locations_and_functions(sentences):
    """
    initialize go-to locations for loops, functions, and classes
    track indices of 'header' sentences (0,1,2,3,...)
    track respective statuses (True/False)
    track loop indices (0,1,2,3,...)
    """
    global goto_locations
    global variable_dictionary
    for i in range(len(sentences)):
        sentence = sentences[i].strip()
        matches_for = re.match('for each (.+) in (.+)', sentence)
        matches_function = re.match('define function (.+) (with |using )(inputs )?(.+)$', sentence)
        matches_class = re.match('define class (.+)', sentence)
        if matches_for:
            goto_locations[i] = Goto_data() # [status, list_index, list_length] = [False, 0, None]
        elif matches_function:
            # add function to goto locations
            goto_info = Goto_data() # [status, list_index, list_length] = [False, 0, None]
            goto_info.name = matches_function.group(1)
            goto_locations[i] = goto_info
            # add function to variable dictionary
            function_name = matches_function.group(1)
            function_variables = matches_function.group(4).split(' and ')
            function = Function_data(i, function_variables)
            print_debug('FUNCTION: ' + function_name + ' (' + str(function_variables) + ')')
            variable_dictionary[function_name] = function
        elif matches_class:
            goto_info = Goto_data() # [status, list_index, list_length] = [False, 0, None]
            goto_locations[i] = goto_info
    print_debug('goto_locations: ' + str(goto_locations))

def run_commands(sentences):
    global nested_blocks_ignore
    i = 0
    while i < len(sentences): # use i to access sentence indices for go-to locations
        print_debug('-------------- LINE #' + str(i+1) + ' --------------'+str(len(goto_stack)))
        sentence = sentences[i]
        sentence = sentence.strip()
        # note: order matters, like order of replacing words or ignoring rest of sentence:
        # note > if > for > function > spell > variable > print > assign > math > import > use
        is_note = check_note(sentence)
        if is_note:
            i += 1
            continue # ignore this sentence
        [nested_blocks_ignore,sentence] = check_if(sentence) # one-liner if-statement may contain sentence to run
        i = check_for(sentence, i) # can skip back to top part of for loop
        [i,nested_blocks_ignore] = check_function(sentence, i) # can skip to top of function or back to where function was called
        if nested_blocks_ignore == 0: # whether to not ignore lines after an if-statement
            sentence = check_spell(sentence)
            sentence = check_variable(sentence) # can replace "variable apple" with the value of apple
            is_print = check_print(sentence)
            if is_print:
                i += 1
                continue # do not try to interpret the rest of the sentence, just go straight to next sentence
            check_assign(sentence)
            sentence = check_math(sentence) # math after assign: avoid creating variables named None
            check_import(sentence)
            i = check_use(sentence, i)
        # print(i+1)
        # print(variable_dictionary)
        # go to next sentence
        i += 1

def get_words(sentence):
    words = sentence.strip().split() # .split() with no params splits at any whitespace character
    return words

"""
example:
Please note this is a comment
"""
def check_note(sentence):
    words = get_words(sentence)
    if words[0] == 'note':
        return True
    else:
        return False

"""
example:
Please print this string of words
"""
def check_print(sentence):
    words = get_words(sentence)
    if words[0] == 'print':
        print(' '.join(words[1:]))
        return True
    else:
        return False

"""
example:
Please spell with the first letters of Neptune unicorn moose panda Yoda
"""
def check_spell(sentence):
    global spell_checkphrases
    global spell_finish_words
    count = 0
    partial_checks = []
    # find matches in sentence:
    for phrase_start in spell_checkphrases:
        for phrase_stop in spell_finish_words:
            checkphrase = '.*' + phrase_start + ' (.+)' + phrase_stop
            matches = re.match(checkphrase, sentence)
            if matches:
                words_to_spell_with = matches.group(1) # this is substring found inside '(.+)'
                spelt_word = spell_with_first_letters(checkphrase, words_to_spell_with)
                print_debug('SPELL: spelt_word=' + spelt_word)
                # print(sentence)
                phrase_to_replace = phrase_start + ' ' + words_to_spell_with
                sentence = sentence.replace(phrase_to_replace, spelt_word + ' ')
                # print(sentence)
    # alternate idea:
        # get indices and then find words between
        # [indices.start() for indices in re.finditer('test', 'test test test test')]
    return sentence

def spell_with_first_letters(checkphrase, sentence):
    local_sent = sentence.replace(checkphrase, '')
    words = local_sent.split()
    spelt_word = ''.join(list(word[0] for word in words))
    return spelt_word

"""
example:
Please create variable apple
Please variable banana
please print you assigned variable apple to apple
"""
def check_variable(sentence):
    global variable_dictionary
    global nested_blocks_ignore
    in_function = False
    if goto_stack:
        function_name = goto_locations[goto_stack[-1][0]].name
        if function_name:
            function = goto_stack[-1][1] # variable_dictionary[function_name]
            in_function = function.being_called
    matches_variable = re.match('.*variable (.+).*', sentence)
    if not matches_variable:
        return sentence
    else:
        variable_name               = matches_variable.group(1) # this is substring found inside '(.+)'
        not_print_statement         = not re.match('print .*', sentence) # avoid creating variables within print statement
        not_return_statement        = not re.match('return .*', sentence) # avoid creating variables within return statements
        not_if_statement            = not re.match('if .*', sentence) # avoid creating variables within if statements
        not_in_certain_statements   = not_return_statement and not_return_statement and not_if_statement
        is_assigning_value          = re.match('assign (.+) to .+',sentence)
        if not in_function and nested_blocks_ignore == 0:
            if variable_name not in variable_dictionary and not_in_certain_statements:
                # NOTE: WORKAROUND: var_name_not_of AND var_name_not_to TO AVOID CREATING VARIABLES WHEN ACTUALLY USING "SUBVARIABLES"
                var_name_not_of = re.match('(.+) of (.+)', variable_name)
                var_name_not_to = re.match('(.+) to (.+)', variable_name)
                if var_name_not_of and var_name_not_to:
                    variable_dictionary[variable_name] = None
                print_debug('variable_dictionary1: ' + str(variable_dictionary))
        elif in_function and nested_blocks_ignore == 0:
            if variable_name not in function.local_variables and variable_name not in variable_dictionary and not_in_certain_statements:
                function.local_variables[variable_name] = None
                if is_assigning_value:
                    function.local_variables[variable_name] = check_math(is_assigning_value.group(1))
                print_debug('function.local_variables['+variable_name+']: ' + str(function.local_variables[variable_name]))
        # if assigning value then don't replace last variable name (after ' to ') because dictionary needs variable name kept in sentence
        matches_assign_to = re.match('(assign .+)( to (variable )?.+)$', sentence) # $ for end of sentence
        replaceable_part = sentence # intialize
        irreplaceable_part = '' # intialize
        if matches_assign_variable:
            replaceable_part    = matches_assign_to.group(1)
            irreplaceable_part  = matches_assign_to.group(2) # put back later
            sentence = replaceable_part
        # print_debug('---1----=='+sentence)
        # check for index of variable name to replace
        checkphrase = '(.*)index (.+) of (variable )?(.+).*'
        matches_variable_index = re.match(checkphrase, sentence)
        if matches_variable_index:
            part_before     = matches_variable_index.group(1)
            index           = matches_variable_index.group(2)
            variable_name   = matches_variable_index.group(4)
            variable_index = eval_math(check_math(index))-1
            if not in_function:
                variable_list = variable_dictionary[variable_name]
            elif in_function:
                if variable_name in function.local_variables:
                    variable_list = function.local_variables[variable_name]
            replacement_phrase = part_before + str(variable_list[variable_index])
            sentence = re.sub(checkphrase, replacement_phrase, sentence)
        if in_function:
            # check for local variable names to replace
            variables_found = dictionary_variables_in_string(sentence, function.local_variables)
            for var_found in variables_found:
                sentence = sentence.replace('variable ' + var_found, str(function.local_variables[var_found]))
        # check for variable names to replace
        variables_found = dictionary_variables_in_string(sentence, variable_dictionary)
        for var_found in variables_found:
            sentence = sentence.replace('variable ' + var_found, str(variable_dictionary[var_found]))
        # put back part that should not have variable replaced
        # print_debug('----2---=='+sentence)
        sentence = sentence + irreplaceable_part
        # print_debug('------3-=='+sentence)
        return sentence

def dictionary_variables_in_string(string, dictionary): # dictionary could be variable_dictionary or local_variables
    # find 'variable <variable_name>' in string for each variable in dictionary
    variables_found = []
    for variable_name in dictionary:
        if re.match('.*variable ' + variable_name+'.*', string):
            variables_found.append(variable_name)
    return variables_found

"""
example:
Please one plus two
"""
def check_math(sentence):
    # if assigning value then don't replace last variable name (after ' to ') because dictionary needs variable name kept in sentence
    matches = re.match('(assign .+)( to (variable )?.+)$', sentence) # $ for end of sentence
    replaceable_part = sentence # intialize
    irreplaceable_part = '' # intialize
    if matches:
        replaceable_part = matches.group(1)
        irreplaceable_part = matches.group(2) # put back later
        sentence = replaceable_part
    words = get_words(sentence)
    math_expression = ''
    replace_expression = ''
    # need to find math expressions word-by-word (since sometimes embedded in sentences like if...then)
    for i in range(len(words)):
        word = words[i]
        if word in math_words_numbers:
            # only do this after non-math word or end of sentence: sentence = sentence.replace(word, str(math_words_numbers[word]))
            math_expression += str(math_words_numbers[word])
            replace_expression += ' ' + word
        elif is_digit(word):
            math_expression += str(word)
            replace_expression += ' ' + word
        elif word in math_words_boolean:
            math_expression += str(math_words_boolean[word])
            replace_expression += ' ' + word
        elif word in math_words_operators:
            math_expression += math_words_operators[word] # already a string
            replace_expression += ' ' + word
        elif word in variable_dictionary:
            variable_value = str(variable_dictionary[word])
            # surround value with quotes if string
            if not variable_value.isdigit():
                variable_value = '\'' + variable_value + '\''
            math_expression += variable_value
            replace_expression += ' variable ' + word
        elif word in ['print','variable','assign','if','then','to','of','from','import','for','as','end','each','in','list','use','function','return']:
            # non-math word detected; time to evaluate expression so far
            try:
                math_result = eval_math(math_expression)
                if math_result:
                    print_debug('MATH1: "' + math_expression + '" -> "' + str(math_result) + '" \t replace_expression = "' + replace_expression + '"')
                    # if the math works, then replace the section of the sentence
                    replace_expression = replace_expression.strip() # to make sure replaces properly
                    sentence = sentence.replace(replace_expression, str(math_result))
            except:
                pass
            # reset variables
            math_expression = ''
            replace_expression = ''
        elif re.match('use .*', sentence):
            pass
        else:
            # surround value with quotes if string
            if not is_digit(word):
                # math_expression += ' \'' + word + '\''
                math_expression += '\'' + word + '\''
                replace_expression += ' ' + word
        # separate if-statement for end of sentence; time to evaluate (may (not) have been a math word)
        if i == len(words)-1:
            try:
                math_result = eval_math(math_expression)
                if math_result:
                    print_debug('MATH2: "' + math_expression + '" -> "' + str(math_result) + '" \t replace_expression = "' + replace_expression + '"')
                    # if the math works, then replace the section of the sentence
                    replace_expression = replace_expression.strip() # to make sure replaces properly
                    sentence = sentence.replace(replace_expression, str(math_result))
                    # print_debug(sentence)
            except:
                pass
            # reset variables
            math_expression = ''
            replace_expression = ''
    sentence = sentence + irreplaceable_part
    return sentence

def is_digit(string):
    # built-in isdigit() doesn't work with negative numbers
    try:
        int(string)
        return True
    except:
        return False

def eval_math(expression):
    # be conservative to try to restrict to only math and avoid abuse
    if ' ' in expression: return None
    if '_' in expression: return None
    if '(' in expression: return None
    if '[' in expression: return None
    return eval(expression,{"__builtins__":None},{}) # use ,{"__builtins__":None},{} to make eval function safer

"""
example:
Please assign one to variable apple
Please assign three hundred to variable banana
Please assign some words to variable coconut
"""
def check_assign(sentence):
    in_function = False
    if goto_stack:
        function_name = goto_locations[goto_stack[-1][0]].name
        if function_name:
            function = variable_dictionary[function_name]
            in_function = function.being_called
    if not check_assign_list_passed(sentence):
        matches = re.match('.*assign (.+) to (variable )?(.+)', sentence)
        if matches:
            variable_value = matches.group(1)
            variable_name = matches.group(3)
            try:
                # try to evaluate math value
                variable_value = eval_math(check_math(variable_value))
            except:
                # it could be a string
                pass
            # check whether to add to local variables dictionary
            if not in_function and nested_blocks_ignore == 0:
                variable_dictionary[variable_name] = variable_value
                print_debug('variable_dictionary2: ' + str(variable_dictionary))
            elif in_function and nested_blocks_ignore == 0:
                function.local_variables[variable_name] = variable_value
                print_debug('function.local_variables: ' + str(function.local_variables))
            # print(' variable_value = ' + str(variable_value) + ' \t variable_name = ' + variable_name)

def check_assign_list_passed(sentence):
    in_function = False
    if goto_stack:
        function_name = goto_locations[goto_stack[-1][0]].name
        if function_name:
            function = variable_dictionary[function_name]
            in_function = function.being_called
    # check if assigning ordered list of items
    matches_list_ordered = re.match('.*assign list from (.+) to (.+) to (variable )?(.+)', sentence)
    if matches_list_ordered:
        list_start      = int(check_math(matches_list_ordered.group(1)))
        list_stop       = int(check_math(matches_list_ordered.group(2)))
        variable_name   = matches_list_ordered.group(4)
        print_debug('list start = ' + str(list_start) + ' stop = ' + str(list_stop) + ' ASSIGN TO: ' + variable_name)
        list_values = list(range(list_start, list_stop+1))
        # check whether to add to local variables dictionary
        if not in_function and nested_blocks_ignore == 0:
            variable_dictionary[variable_name] = list_values
            print_debug('variable_dictionary3: ' + str(variable_dictionary))
        elif in_function and nested_blocks_ignore == 0:
            function.local_variables[variable_name] = list_values
            print_debug('function.local_variables: ' + str(function.local_variables))
        return True # found assignment of list to variable
    # check if assigning unordered list of items separated by ' and '
    matches_list_unordered = re.match('.*assign list of (.+) to (variable )?(.+)', sentence)
    if matches_list_unordered:
        variable_name           = matches_list_unordered.group(3)
        unordered_list_items    = matches_list_unordered.group(1).split(' and ') # items separated by ' and '
        unordered_list_items    = translate_list_items(unordered_list_items)
        print_debug('list unordered_list_items = ' + str(unordered_list_items) + ' ASSIGN TO: ' + variable_name)
        # check whether to add to local variables dictionary
        if not in_function and nested_blocks_ignore == 0:
            variable_dictionary[variable_name] = unordered_list_items
            print_debug('variable_dictionary4: ' + str(variable_dictionary))
        elif in_function and nested_blocks_ignore == 0:
            function.local_variables[variable_name] = unordered_list_items
            print_debug('function.local_variables: ' + str(function.local_variables))
        return True # found assignment of list to variable
    return False # did not find assignment of list to variable

def translate_list_items(list_items):
    # check if any list items fall under math, variables, or spelled words
    for i in range(len(list_items)):
        item = list_items[i]
        try:
            list_items[i] = int(check_math(item))
        except:
            list_items[i] = check_variable(check_spell(item))
    return list_items

"""
example:
Please import alternate
Please import test from library
Please import numpy as nectarine pony
"""
def check_import(sentence):
    global import_dictionary
    module = None 
    matches = re.match('.*import (.+)(( as (.+))|( from (.+)))', sentence)
    if matches:
        import_name = matches.group(1)
        import_as = matches.group(4)
        import_from = matches.group(6)
        print_debug('IMPORT:\n\timport_name = ' + str(import_name) + '\n\timport_from = ' + str(import_from) + '\n\timport_as = ' + str(import_as))
        if import_as: # can nickname import module
            print_debug('IMPORT ... AS ...')
            module = import_module(import_name)
        if import_from: # can import from folder
            print_debug('IMPORT ... FROM ...')
            spec = importlib.util.spec_from_file_location(import_name, import_from + '/' + import_name + '.py')
            module = importlib.util.module_from_spec(spec)
            # enables use of functions and variables from the module (does the actual import):
            spec.loader.exec_module(module)
        print_debug('IMPORT: ' + str(module))
        # add to list of imports
        if import_as:
            import_dictionary[import_as] = module
        else:
            import_dictionary[import_name] = module
        print_debug('IMPORT: IMPORT_DICTIONARY, size = ' + str(len(import_dictionary)) + '\n\t = ' + str(import_dictionary))
    else:
        matches = re.match('.*import (.+)', sentence)
        if matches:
            print_debug('IMPORT NAME ...')
            import_name = matches.group(1).strip() # remove final spaces because of regex
            try: # try with .py ending
                spec = importlib.util.spec_from_file_location(import_name, import_name + '.py')
                module = importlib.util.module_from_spec(spec)
                # enables use of functions and variables from the module (does the actual import):
                spec.loader.exec_module(module)
            except:
                try: # try withOUT .py ending
                    spec = importlib.util.spec_from_file_location(import_name, import_name)
                    module = importlib.util.module_from_spec(spec)
                    # enables use of functions and variables from the module (does the actual import):
                    spec.loader.exec_module(module)
                except:
                    pass
            print_debug('IMPORT: ' + str(module))
            # add to list of imports
            import_dictionary[import_name] = module
            print_debug('IMPORT: IMPORT_DICTIONARY, size = ' + str(len(import_dictionary)) + '\n\t = ' + str(import_dictionary))

"""
example 1:
Please use test_function of test
Please use test_function from test
"""
"""
example 2:
please define function test with item
    please print variable item
please end function
please assign it works to other
please use function test on variable other
"""
def check_use(sentence, i):
    i = check_use_functions_imported(sentence, i)
    i = check_use_functions_user_defined(sentence, i)
    return i
    
def check_use_functions_imported(sentence, i):
    # check even more restrictive one first
    # assign ouput of imported function given input values/variables
    matches_input_and_output = re.match('.*use (.+)( from | of )(.+)( on (.+)) to (variable )?(.+)', sentence)
    if matches_input_and_output:
        use_string      = matches_input_and_output.group(1)
        from_string     = matches_input_and_output.group(3).replace(' ','') # remove spaces in import names for now
        input_variables = matches_input_and_output.group(5).split(' and ') # later convert to args list with a star: *input_variables
        variable_name   = matches_input_and_output.group(7)
        print_debug('USE: ' + use_string + '\n  from ' + from_string + '\n  on ' + str(input_variables) + '\n  to ' + variable_name)
        function_imported = getattr(import_dictionary[from_string], use_string)
        try:
            variable_dictionary[variable_name] = function_imported(*input_variables) # try to use function_imported as a function
            print_debug('variable_dictionary5: ' + str(variable_dictionary))
        except:
            print(function_imported) # in case function_imported is just an output value
            variable_dictionary[variable_name] = function_imported # in case function_imported is just an output value
            print_debug('variable_dictionary6: ' + str(variable_dictionary))
        return i
    # check more restrictive one first
    # assign output of imported function to variable
    matches_output_only = re.match('.*use (.+)( from | of )(.+) to (.+)', sentence)
    if matches_output_only:
        use_string      = matches_output_only.group(1)
        from_string     = matches_output_only.group(3)
        variable_name   = matches_output_only.group(4)
        print_debug('USE: ' + use_string + ' from ' + from_string + ' to ' + variable_name)
        function_imported = getattr(import_dictionary[from_string], use_string)
        try:
            variable_dictionary[variable_name] = function_imported() # try to use function_imported as a function
            print_debug('variable_dictionary7: ' + str(variable_dictionary))
        except:
            print(function_imported) # in case function_imported is just an output value
            variable_dictionary[variable_name] = function_imported # in case function_imported is just an output value
            print_debug('variable_dictionary8: ' + str(variable_dictionary))
        return i
    # check less restrictive one after
    # use imported function
    matches_no_input_or_output = re.match('.*use (.+)( from | of )(.+)', sentence)
    if matches_no_input_or_output:
        use_string  = matches_no_input_or_output.group(1)
        from_string = matches_no_input_or_output.group(3)
        print_debug('USE: ' + use_string + ' from ' + from_string)
        function_imported = getattr(import_dictionary[from_string], use_string)
        try:
            function_imported() # try to use function_imported as a function
        except:
            print(function_imported) # in case function_imported is just an output value
        return i
    # otherwise no change to i
    return i

def check_use_functions_user_defined(sentence, i):
    function_name = ''
    input_values = [None]
    output_variable = ''
    # check for output variable to assign value to
    matches_input_and_output = re.match('.*use function (.+) (on|with) (.+) to (variable )?(.+)', sentence)
    if matches_input_and_output:
        output_variable = matches_input_and_output.group(5)
        function_name   = matches_input_and_output.group(1)
        input_values    = matches_input_and_output.group(3).split(' and ')
        print_debug('function_name1 = ' + str(function_name) + ' : input_values = ' + str(input_values) + ' : output_variable = ' + str(output_variable))
    # check use of function from variable_dictionary, with or without input values
    # check more restrictive phrasing first
    matches_with_input = re.match('.*use function (.+) (on|with) (.+)', sentence)
    if not matches_input_and_output:
        if matches_with_input:
            function_name   = matches_with_input.group(1)
            input_values    = matches_with_input.group(3).split(' and ')
            print_debug('function_name2 = ' + str(function_name) + ' : input_values = ' + str(input_values))
        else:
            # check less restrictive phrasing after
            matches_without_input = re.match('.*use function (.+)', sentence)
            if matches_without_input:
                function_name = matches_without_input.group(1)
                # input_values = [None]
                print_debug('function_name3 = ' + str(function_name) + ' : (no input_values)')
    # either way, try to find function index and then skip to top of function
    if matches_with_input or matches_without_input:
        for index in goto_locations:
            if goto_locations[index].name == function_name:
                print_debug('CALL FUNCTION: ' + function_name)
                function = copy.deepcopy(variable_dictionary[function_name]) # variable_dictionary[function_name] would point to same object
                function.activate(input_values, i)
                function.output_variable = output_variable
                goto_stack.append([index,function])
                # change output i if function found
                i = index
        return i
    # otherwise no change to i
    return i

"""
example:
Please if true then print this is a one line if statement
Please if one equals one then
    Please print it works
Please end if
Please if one equals two then
    Please print it should not print this
Please end if
"""
def check_if(sentence): # TO-DO: track number of if-statements and end-ifs (nesting)
    global nested_blocks_ignore
    # force 'if' to be first word; DO NOT start regex with '.*'
    matches = re.match('if (.+) then$', sentence) # $ for end of sentence
    matches_oneliner = re.match('(if (.+) then ).+', sentence) # space after WITHOUT $ for continuing sentence
    if matches:
        put_in_vals_of_vars = check_variable(check_spell(matches.group(1)))
        math_expression = check_math(put_in_vals_of_vars)
        if math_expression not in ['True', 'False']:
            math_expression = 'False'
        if_string = eval_math(math_expression)
        print_debug('if (' + str(if_string) + ') then')
        if if_string == True and nested_blocks_ignore == 0:
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- if')
            return [nested_blocks_ignore,sentence]
        else:
            print_debug('-> FALSE -> end if')
            nested_blocks_ignore += 1
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- if')
            return [nested_blocks_ignore,sentence]
    elif matches_oneliner:
        # treat the rest of the sentence like a new sentence
        put_in_vals_of_vars = check_variable(check_spell(matches_oneliner.group(2)))
        math_expression = check_math(put_in_vals_of_vars)
        if math_expression not in ['True', 'False']:
            math_expression = 'False'
        if_string = eval_math(math_expression)
        print_debug('if (' + str(if_string) + ') then')
        if if_string == True and nested_blocks_ignore == 0:
            # run the rest of this sentence as its own command (make sure check_if() happens before other checks)
            sentence = sentence.replace(matches_oneliner.group(1), '')
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- if')
            return [nested_blocks_ignore,sentence]
        else:
            print_debug('-> FALSE -> end if')
            # one-liner if-statement does not add to nestedness, so do not do nested_blocks_ignore += 1
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- if')
            return [nested_blocks_ignore,sentence]
    else:
        matches = re.match('.*end if', sentence)
        if not matches:
            return [nested_blocks_ignore,sentence]
        else:
            nested_blocks_ignore -= 1
            if nested_blocks_ignore < 0:
                nested_blocks_ignore = 0
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- end if')
            return [nested_blocks_ignore,sentence]

"""
example:
Please assign list from negative one to three to variable circle
Please for each index in circle
    Please print variable index
Please end for
"""
def check_for(sentence, i):
    global nested_blocks_ignore
    skip_to_line = i
    matches = re.match('for each (variable )?(.+) in (variable )?(.+)', sentence)
    if matches:
        element = matches.group(2)
        list_name = matches.group(4)
        print_debug('FOR: sentence = '+sentence)
        print_debug('FOR: element = ' + element)
        print_debug('FOR: list_name = ' + list_name)
        # create loop variable for element to go through the list range
        variable_dictionary[element] = variable_dictionary[list_name][0]
        print_debug('VAR DICT: ' + str(variable_dictionary))
        # activate this loop (no need to evaluate true right now)
        current_loop = goto_locations[i]
        current_loop.activate(element, variable_dictionary[list_name])
        print_debug('GOTO STATUS: ' + str(goto_locations[i].status))
        # track nesting
        goto_stack.append([i,current_loop])
        print_debug('GOTO STACK: ' + str(goto_stack))
        # don't skip anywhere
        skip_to_line = i
    else:
        matches = re.match('end for', sentence)
        if not matches:
            # don't skip anywhere
            skip_to_line = i
        else: # check if need to loop back to header index
            last_nested_i = goto_stack[-1][0]
            current_loop = goto_locations[last_nested_i]
            # check if at last index in list_name
            loop_index = current_loop.list_index
            print_debug('FOR list len: '+str(current_loop.list_length))
            if loop_index >= current_loop.list_length-1:
                # remove loop variable
                element = current_loop.loop_variable
                variable_dictionary.pop(element)
                print_debug('VAR DICT: ' + str(variable_dictionary))
                # deactivate this loop
                current_loop.deactivate()
                print_debug('GOTO STATUS: ' + str(goto_locations[last_nested_i].status))
                goto_stack.pop()
                print_debug('GOTO STACK: ' + str(goto_stack))
                # don't skip anywhere
                skip_to_line
            else:
                current_loop.list_index += 1
                variable_dictionary[current_loop.loop_variable] += 1
                # skip back to the beginning of loop
                skip_to_line = last_nested_i
    return skip_to_line

"""
example:
Please define function test with item
    Please print variable item
Please end function
Please assign it works to other
Please use function test on variable other
"""
def check_function(sentence, i):
    global nested_blocks_ignore
    # input names expected to be separated by ' and '
    matches = re.match('define function (.+)( with | using )(inputs )?(.+)$', sentence)
    if matches:
        function_name = matches.group(1)
        input_names = matches.group(4).split(' and ')
        print_debug('FUNCTION: ' + function_name + ' (' + str(input_names) + ')')
        # check if function not being called
        function = variable_dictionary[function_name]
        if not function.being_called: # (just carry on reading linearly if it is being called)
            nested_blocks_ignore += 1
        return [i, nested_blocks_ignore]
    # check end function and setting nested_blocks_ignore -= 1 or = 0
    if re.match('end function', sentence):
        # if ignoring current function insides, can stop ignoring it now
        nested_blocks_ignore -= 1
        if nested_blocks_ignore < 0:
            nested_blocks_ignore = 0
        # check if there's anything on the goto_stack (like for loop or function)
        if goto_stack:
            # get last goto stack item index because such goto blocks can only be within each other
            index = goto_stack[-1][0]
            function_name = goto_locations[index].name
            function = goto_stack[-1][1] #variable_dictionary[function_name]
            if function.being_called:
                # get index of where function was called
                i = function.index_called_from
                # then remove function from call stack
                goto_stack.pop()
                print_debug('END FUNCTION: called from i = '+str(i))
    # check return statement and setting nested_blocks_ignore -= 1 or = 0
    matches = re.match('return (variable )?(.+)', sentence)
    if matches:
        output_value = check_math(matches.group(2)) # will either output the literal value "...", or the value of "variable ..."
        outputting_variable_value = matches.group(1)
        # check if there's anything on the goto_stack (like for loop or function)
        if goto_stack:
            # get last goto stack item index because such goto blocks can only be within each other
            index = goto_stack[-1][0]
            function_name = goto_locations[index].name
            function = goto_stack[-1][1] #variable_dictionary[function_name]
            print_debug('function.local_variables = '+str(function.local_variables))
            print_debug('variable_dictionary = '+str(variable_dictionary))
            if function.being_called:
                # if ignoring current function insides, can stop ignoring it now
                nested_blocks_ignore -= 1
                if nested_blocks_ignore < 0:
                    nested_blocks_ignore = 0
                if output_value: # (otherwise could just be "please return")
                    if outputting_variable_value:
                        # cover both "please return variable ..." and "please return ..."
                        output_value = function.local_variables[output_value]
                    # output return value
                    output_variable = function.output_variable
                    if len(goto_stack) == 1: # TODO currently assume no function calling current function, so just outputting to global variable_dictionary
                        variable_dictionary[output_variable] = output_value
                    else:
                        is_a_function = goto_stack[-2][1].local_variables
                        if is_a_function:
                            goto_stack[-2][1].local_variables[output_variable] = output_value
                # get index of where function was called
                i = function.index_called_from
                # then remove function from call stack
                goto_stack.pop()
                print_debug('RETURN FUNCTION: called from line #'+str(i+1) + ' : output =' + str(output_value) + ' --> variable =' + output_variable)
    print_debug('FUNCTION: goto_stack: '+str(goto_stack))
    # print(variable_dictionary)
    return [i, nested_blocks_ignore]

def print_debug(string):
    if hide_debug_printouts == False:
        print('  DEBUG ' + string)



# initialize global variables:

nested_blocks_ignore = 0 # track nesting to know whether got out of an if-statement that evaluated to False (to ignore lines)
goto_stack = [] # append/pop "header" indices to track nesting of loops, functions, or classes ; [#,#,#,...]
# goto_stack may have multiple copies of a function if there's recursion

# Python dictionaries are hashtables (avg time complexity O(1)):
goto_locations = {} # map indices to Goto_data of loops, functions, and classes ; {#:<Goto_data()>, #:<Goto_data()>,...}
variable_dictionary = {} # map variable names to variable values ; {'...':#, '...':'...', ...}
import_dictionary = {} # map import names to import modules ; {'...':<...>, '...':<...>, ...}

# classes to group together variables and setup steps:
class Goto_data:
    status = False
    name = '' # functions
    list_index = 0 # for loops
    loop_variable = '' # for loops
    list_length = None # for loops
    def activate(self, element, list_name):
        self.status = True
        self.loop_variable = element
        self.list_length = len(list_name)
    def deactivate(self):
        self.status = False
        self.list_index = 0
        self.loop_variable = ''
class Function_data:
    # set once:
    location = None
    ordered_names = []
    # set values each time call function:
    being_called = False
    local_variables = {} # (except local variable names are set at beginning)
    index_called_from = None
    output_variable = ''
    def __init__(self, location, list_of_variable_names):
        self.location = location
        for variable in list_of_variable_names:
            self.local_variables[variable] = None
            self.ordered_names.append(variable)
    def activate(self, list_of_input_values, index_called_from):
        self.being_called = True # TODO: being_called is unnecessary for functions since using a separate goto_stack; remove this prop from variable_dictionary too?
        if list_of_input_values:
            for i in range(len(list_of_input_values)):
                self.local_variables[self.ordered_names[i]] = list_of_input_values[i]
        self.index_called_from = index_called_from

# recognize words for numbers, math operations, spelling checkphases, etc.
math_words_numbers = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,
                      'six':6,'seven':7,'eight':8,'nine':9,'ten':10,
                      'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,
                      'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19,
                      'twenty':20,'thirty':30,'forty':40,'fifty':50,
                      'sixty':60,'seventy':70,'eighty':80,'ninety':90,
                      'hundred':'00','thousand':'000','million':'000000',
                      'billion':'000000000','trillion':'000000000',
                      '0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9}
math_words_boolean = {'true':True,'false':False}
math_words_operators = {'plus':'+','positive':'+','minus':'-','negative':'-',
                        'times':'*','divide':'/','divided':'/',
                        'equals':'==','equal':'==','over':'>','above':'>','under':'<','below':'<',
                        'not':'!',
                        'modulus':'%','modulo':'%'} # add more functions later as needed
spell_checkphrases = ['spell with first letters of',
                      'spell with first letter of',
                      'spelled with first letters of',
                      'spelled with first letter of',
                      'spell with the first letters of',
                      'spell with the first letter of',
                      'spelled with the first letters of',
                      'spelled with the first letter of',
                      'spell using the first letters of',
                      'spell using the first letter of',
                      'spelled using the first letters of',
                      'spelled using the first letter of',
                      'spelt with the first letters of',
                      'spelt with the first letter of',
                      'spelt using the first letters of',
                      'spelt using the first letter of',
                     ]
spell_finish_words = ['to', 'as', 'from', 'then', '$'] # $ for end of line for regex

# True = hide debug prints:
# False = show debug prints:
hide_debug_printouts = True



# (this if statement lets code after it only run if you're running this file directly)
if __name__ == '__main__':
    print('\nPLEASE WORK...\n')
    # run this interpreter:
    interpret()
    print('\n...THANK YOU!\n')
    print(str(variable_dictionary))
    print(str(import_dictionary))