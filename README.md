# "Please" - a programming language

I want to try to create a programming language that can use (i.e. parse) text generated by Mac Dictation.

Python is great, but I want to experiment with parsing text that doesn't use special characters (like quotation marks) that would require typing or special recognition by Mac Dictation.

I.e., use only letters and the space character (the word 'spacebar' is recognized by Mac Dictation).

Each new sentence starts with "please" and roughly corresponds to a new command in code.

# Use:

Download this project, open the folder in Terminal/Commandline, and type:

    python interpreter.py text.txt

# Example code in "Please":

    Please print this string of words

This prints out:

    this string of words

# Ideas for Development:

* Try to import existing python libraries like numpy.

* Try to be able to enter words that are likely to not be trained into Mac Dictation by default (like the word 'numpy'). How? Maybe use some kind of spelling convention, like using the first letters of the words 'neptune unicorn moose panda yak' --> 'numpy'.

# Inspirations for "Please":

https://github.com/hchiam/programmingByVoice

https://github.com/AnotherTest/-English

https://www.youtube.com/playlist?list=PLBOh8f9FoHHiKx3ZCPxOZWUtZswrj2zI0
