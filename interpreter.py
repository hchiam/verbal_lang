# interpret() function is where you should start reading to understand this code.
# interpret() has to be called at the bottom of this file for things to work.

from sys import *
import re
from importlib import import_module
import importlib.util



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
        if matches_function:
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
        elif matches_for:
            goto_locations[i] = Goto_data() # [status, list_index, list_length] = [False, 0, None]
    print_debug('goto_locations: ' + str(goto_locations))

def run_commands(sentences):
    global nested_blocks_ignore
    i = 0
    while i < len(sentences): # use i to access sentence indices for go-to locations
        print_debug('LINE #' + str(i+1) + ' --------------')
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
    local_var_dictionary = {}
    in_function = False
    if goto_stack:
        function_name = goto_locations[goto_stack[-1]].name
        if function_name:
            function = variable_dictionary[function_name]
            in_function = function.being_called
            if in_function:
                local_var_dictionary = function.local_variables
    matches = re.match('.*variable (.+).*', sentence)
    if matches:
        variable_name = matches.group(1) # this is substring found inside '(.+)'
        not_print_statement = not re.match('print .*', sentence) # avoid creating variables within print statement
        assigning_value = re.match('assign .+ to .+',sentence)
        if not in_function:
            if variable_name not in variable_dictionary and not_print_statement and not assigning_value:
                variable_dictionary[variable_name] = None
                print_debug('variable_dictionary1: ' + str(variable_dictionary))
        elif in_function:
            if variable_name not in local_var_dictionary and variable_name not in variable_dictionary and not_print_statement and not assigning_value:
                local_var_dictionary[variable_name] = None
                print_debug('local_var_dictionary: ' + str(local_var_dictionary))
        # if assigning value then don't replace last variable name (after ' to ') because dictionary needs variable name kept in sentence
        matches = re.match('(.+)( to (variable )?.+)$', sentence) # $ for end of sentence
        replaceable_part = sentence # intialize
        irreplaceable_part = '' # intialize
        if matches:
            replaceable_part = matches.group(1)
            irreplaceable_part = matches.group(2)
            sentence = replaceable_part
        # print_debug('---1----=='+sentence)
        # check for index of variable name to replace
        checkphrase = '(.*)index (.+) of (variable )?(.+).*'
        matches = re.match(checkphrase, sentence)
        if matches:
            part_before = matches.group(1)
            index = matches.group(2)
            variable_name = matches.group(4)
            variable_index = eval_math(check_math(index))-1
            if variable_name in local_var_dictionary:
                variable_list = local_var_dictionary[variable_name]
            else:
                variable_list = variable_dictionary[variable_name]
            replacement_phrase = part_before + str(variable_list[variable_index])
            sentence = re.sub(checkphrase, replacement_phrase, sentence)
        # check for variable names to replace
        variables_found = dictionary_variables_in_string(sentence, local_var_dictionary)
        for var_found in variables_found:
            sentence = sentence.replace('variable ' + var_found, str(local_var_dictionary[var_found]))
        # check for variable names to replace
        variables_found = dictionary_variables_in_string(sentence, variable_dictionary)
        for var_found in variables_found:
            sentence = sentence.replace('variable ' + var_found, str(variable_dictionary[var_found]))
        # put back part that should not have variable replaced
        # print_debug('----2---=='+sentence)
        sentence = sentence + irreplaceable_part
        # print_debug('------3-=='+sentence)
        return sentence
    else:
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
        elif word not in ['print','variable','assign','if','then','to','of','from','import','for','as','end','each','in','list','use']: # non-math word detected; time to evaluate expression so far
            try:
                math_result = eval_math(math_expression)
                print_debug('MATH1: ' + math_expression + ' -> ' + str(math_result) + ' \t replace_expression = ' + replace_expression)
                # if the math works, then replace the section of the sentence
                replace_expression = replace_expression.strip() # to make sure replaces properly
                sentence = sentence.replace(replace_expression, str(math_result))
            except:
                pass
            # reset variables
            math_expression = ''
            replace_expression = ''
        # separate if-statement for end of sentence; time to evaluate (may (not) have been a math word)
        if i == len(words)-1:
            try:
                math_result = eval_math(math_expression)
                print_debug('MATH2: ' + math_expression + ' -> ' + str(math_result) + ' \t replace_expression = ' + replace_expression)
                # if the math works, then replace the section of the sentence
                replace_expression = replace_expression.strip() # to make sure replaces properly
                sentence = sentence.replace(replace_expression, str(math_result))
            except:
                pass
            # reset variables
            math_expression = ''
            replace_expression = ''
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
            variable_dictionary[variable_name] = variable_value
            # print(' variable_value = ' + str(variable_value) + ' \t variable_name = ' + variable_name)
            print_debug('variable_dictionary2: ' + str(variable_dictionary))

def check_assign_list_passed(sentence):
    # check if assigning ordered list of items
    matches = re.match('.*assign list from (.+) to (.+) to (variable )?(.+)', sentence)
    if matches:
        list_start = int(check_math(matches.group(1)))
        list_stop = int(check_math(matches.group(2)))
        variable_name = matches.group(4)
        print_debug('list start = ' + str(list_start) + ' stop = ' + str(list_stop) + ' ASSIGN TO: ' + variable_name)
        list_values = list(range(list_start, list_stop+1))
        variable_dictionary[variable_name] = list_values
        print_debug('variable_dictionary3: ' + str(variable_dictionary))
        return True # found assignment of list to variable
    # check if assigning unordered list of items separated by ' and '
    matches = re.match('.*assign list of (.+) to (variable )?(.+)', sentence)
    if matches:
        unordered_list_items = matches.group(1).split(' and ') # items separated by ' and '
        unordered_list_items = translate_list_items(unordered_list_items)
        variable_name = matches.group(3)
        print_debug('list unordered_list_items = ' + str(unordered_list_items) + ' ASSIGN TO: ' + variable_name)
        variable_dictionary[variable_name] = unordered_list_items
        print_debug('variable_dictionary4: ' + str(variable_dictionary))
        return True # found assignment of list to variable
    # TODO: '.*assign list of (.+) to (variable )?(.+)' --> group(1) --> .split(' and ') --> 'one and two and tree bark' -> [one,two,'tree bark']
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
    global import_dictionary
    # check even more restrictive one first
    # assign ouput of imported function given input value/variable
    matches = re.match('.*use (.+)( from | of )(.+)( on (.+)) to (.+)', sentence)
    if matches:
        use_string = matches.group(1)
        from_string = matches.group(3)
        input_variables = matches.group(5)
        variable_name = matches.group(6)
        print_debug('USE: ' + use_string + '\n  from ' + from_string + '\n  on ' + input_variables + '\n  to ' + variable_name)
        function_imported = getattr(import_dictionary[from_string], use_string)
        try:
            variable_dictionary[variable_name] = function_imported(input_variables) # try to use function_imported as a function
            print_debug('variable_dictionary5: ' + str(variable_dictionary))
        except:
            print(function_imported) # in case function_imported is just an output value
            variable_dictionary[variable_name] = function_imported # in case function_imported is just an output value
            print_debug('variable_dictionary6: ' + str(variable_dictionary))
        return i
    # check more restrictive one first
    # assign output of imported function to variable
    matches = re.match('.*use (.+)( from | of )(.+) to (.+)', sentence)
    if matches:
        use_string = matches.group(1)
        from_string = matches.group(3)
        variable_name = matches.group(4)
        print_debug('USE: ' + use_string + ' from ' + from_string + ' to ' + variable_name)
        function_imported = getattr(import_dictionary[from_string], use_string)
        try:
            variable_dictionary[variable_name] = function_imported() # try to use function_imported as a function
            print_debug('variable_dictionary5: ' + str(variable_dictionary))
        except:
            print(function_imported) # in case function_imported is just an output value
            variable_dictionary[variable_name] = function_imported # in case function_imported is just an output value
            print_debug('variable_dictionary6: ' + str(variable_dictionary))
        return i
    # check less restrictive one after
    # use imported function
    matches = re.match('.*use (.+)( from | of )(.+)', sentence)
    if matches:
        use_string = matches.group(1)
        from_string = matches.group(3)
        print_debug('USE: ' + use_string + ' from ' + from_string)
        function_imported = getattr(import_dictionary[from_string], use_string)
        try:
            function_imported() # try to use function_imported as a function
        except:
            print(function_imported) # in case function_imported is just an output value
        return i
    # check use of function from variable_dictionary
    function_name = ''
    input_values = [None]
    matches_with_inputs = re.match('.*use function (.+) (on|with) (.+)', sentence) # check more restrictive phrasing first
    if matches_with_inputs:
        function_name = matches_with_inputs.group(1)
        input_values = matches_with_inputs.group(3).split(' and ')
        print_debug('function_name = ' + str(function_name) + ' : input_values = ' + str(input_values))
    else:
        matches_without_inputs = re.match('.*use function (.+)', sentence) # check less restrictive phrasing after
        if matches_without_inputs:
            function_name = matches_without_inputs.group(1)
            # input_values = [None]
            print_debug('function_name = ' + str(function_name) + ' : (no input_values)')
    # either way, try to find function index and then skip to top of function
    if matches_with_inputs or matches_without_inputs:
        for index in goto_locations:
            if goto_locations[index].name == function_name:
                print_debug('CALL FUNCTION: ' + function_name)
                function = variable_dictionary[function_name]
                function.activate(input_values, i)
                goto_stack.append(index)
                # change output i if function found
                i = index
        return i
    # if not using any function, then no change to i
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
    matches_oneliner = re.match('if (.+) then ', sentence) # space after WITHOUT $ for continuing sentence
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
        put_in_vals_of_vars = check_variable(check_spell(matches_oneliner.group(1)))
        math_expression = check_math(put_in_vals_of_vars)
        if math_expression not in ['True', 'False']:
            math_expression = 'False'
        if_string = eval_math(math_expression)
        print_debug('if (' + str(if_string) + ') then')
        if if_string == True and nested_blocks_ignore == 0:
            # run the rest of this sentence as its own command (make sure check_if() happens before other checks)
            sentence = sentence.replace(matches_oneliner.group(), '')
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- if')
            return [nested_blocks_ignore,sentence]
        else:
            print_debug('-> FALSE -> end if')
            # one-liner if-statement does not add to nestedness, so do not do nested_blocks_ignore += 1
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- if')
            return [nested_blocks_ignore,sentence]
    else:
        matches = re.match('.*end if', sentence)
        if matches:
            nested_blocks_ignore -= 1
            if nested_blocks_ignore < 0:
                nested_blocks_ignore = 0
            # print_debug('nested_blocks_ignore: '+str(nested_blocks_ignore) + ' --- end if')
            return [nested_blocks_ignore,sentence]
        else:
            return [nested_blocks_ignore,sentence]

"""
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
        goto_stack.append(i)
        print_debug('GOTO STACK: ' + str(goto_stack))
        # don't skip anywhere
        skip_to_line = i
    else:
        matches = re.match('end for', sentence)
        if matches: # check if need to loop back to header index
            last_nested_i = goto_stack[-1]
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
        else:
            # don't skip anywhere
            skip_to_line = i
    return skip_to_line

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
    if re.match('.*end function', sentence):
        # if ignoring current function insides, can stop ignoring it now
        nested_blocks_ignore -= 1
        if nested_blocks_ignore < 0:
            nested_blocks_ignore = 0
        # check if there's anything on the goto_stack (like for loop or function)
        if goto_stack:
            # get last goto stack item index because such goto blocks can only be within each other
            index = goto_stack[-1]
            function_name = goto_locations[index].name
            function = variable_dictionary[function_name]
            if function.being_called:
                # get index of where function was called
                i = function.index_called_from
                # then reset function local variables etc.
                function.deactivate()
                goto_stack.pop()
                print_debug('END FUNCTION: called from i = '+str(i))
    print_debug('FUNCTION: goto_stack: '+str(goto_stack))
    return [i, nested_blocks_ignore]

def print_debug(string):
    if hide_debug_printouts == False:
        print('  DEBUG ' + string)



# initialize global variables:

hide_debug_printouts = True # True = hide debug prints
goto_stack = [] # append/pop "header" indices to track nesting of loops, functions, or classes ; {#,#,#,...}
goto_locations = {} # map indices to Goto_data of loops, functions, and classes ; {#:<Goto_data()>,#:<Goto_data()>,...}
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
nested_blocks_ignore = 0 # to track whether got out of an if-statement that evaluated to False
variable_dictionary = {} # Python dictionaries are just hashtables (avg time complexity O(1))
import_dictionary = {}
class Function_data:
    # set once:
    location = None
    ordered_names = []
    # set values each time call function:
    being_called = False
    local_variables = {} # (except local variable names are set at beginning)
    index_called_from = None
    def __init__(self, location, list_of_variable_names):
        self.location = location
        for variable in list_of_variable_names:
            self.local_variables[variable] = None
            self.ordered_names.append(variable)
    def activate(self, list_of_input_values, index_called_from):
        self.being_called = True
        if list_of_input_values:
            for i in range(len(list_of_input_values)):
                self.local_variables[self.ordered_names[i]] = list_of_input_values[i]
        self.index_called_from = index_called_from
    def deactivate(self):
        self.being_called = False
        for name in self.local_variables:
            self.local_variables[name] = None
        self.index_called_from = None
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



# (this if statement lets code after it only run if you're running this file directly)
if __name__ == '__main__':
    print('\nPLEASE WORK...\n')
    # run this interpreter:
    interpret()
    print('\n...THANK YOU!\n')
    