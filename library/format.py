# code text formatter
# Puts "please" at every new line

"""
FUTURE: Puts indents when it sees if-statements (and later for-loops, and de-indents at any end-if's).
"""

from sys import *
from importlib import import_module
import importlib.util


progress_bar = 0

def clean():
    file_name = 'text.txt'
    text = ''
    print('\n---Formatter Starting---\n')
    # first try getting from folder above
    file_name_dir = '../text.txt'
    try:
        text = get_text(file_name_dir)
    except:
        # then try getting from local folder
        try:
            file_name_dir = 'text.txt'
            text = get_text(file_name_dir)
        except:
            print('\n***FILE NOT FOUND***\n')
    update_progress_bar_display()
    text = reformat(text)
    rewrite_file(file_name, text)
    print('\n---Formatter Finished---\n')

def get_text(file_name):
    # with open(file_name, 'r') as f:
    #     text = f.readlines()
    # return text
    # just get one long string to parse
    return open(file_name, 'r').read()

def reformat(text):
    # put each "please" at new lines
    text = text.lower().replace(' please','\nplease') # just one long string to parse
    
    # FUTURE: put indents when it sees if-statements (and later for-loops, and de-indents at any end-if's).
    text = format_lines(text)
    
    return text

def format_lines(text):
    # edit line by line instead of as one long string (so can track indents)
    sentences = text.split('please')[1:] # index 0 is []
    text = ''
    num_indents = 0
    for sentence in sentences:
        # immediately de-indent an end-if line
        if sentence[:7] == ' end if':
            num_indents -= 1
        # add indents as needed and remove multiple consecutive space characters per line
        text += '\t'*num_indents + 'please ' + remove_multi_spaces(sentence) + '\n'
        # indent the next line after an if-statement
        if sentence[:4] == ' if ':
            num_indents += 1
    return text

def remove_multi_spaces(sentence):
    return ' '.join(sentence.split())

def rewrite_file(file_name, text):
    new_file_name = file_name[:-4]+'_FORMATTED.txt'
    # create or clear formatted file
    open(new_file_name, 'w').write('')
    # append each new line of text
    for line in text:
        with open(new_file_name, 'a') as f:
            f.write(line)
            update_progress_bar_display()

def update_progress_bar_display():
    global progress_bar
    progress_bar += 1
    # print(str(progress_bar) + ' .........Still Formatting.........')


if __name__ == '__main__': # only perform the following if running this file directly
    clean()
