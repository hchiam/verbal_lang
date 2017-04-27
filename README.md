# "Please" - an experimental programming language

Please can read (i.e. parse) text generated by speech recognition software (like Mac Dictation), so you can code by talking.

# Example code in Please:

First transcribe this code:

    Please print this string of words

When you run that code, it prints out:

    this string of words

# Use:

Download this project, open the folder in Terminal/Commandline, and type:

    python interpreter.py text.txt

You can find the example "source code" in text.txt.

# Why?

What if code could be easy to read and be *more* like English sentences? What if you could easily write code just by talking with speech recognition software? How might you combine these two things (easy-to-read and easy-to-say code)?

Please is an attempt at that.

Here are 3 ground rules to make commands easier to say, but also easier for speech recognition software and Please's code interpreter to understand:

* **Just say words that use your ABCs and spaces between**. No special non-letter characters like "?". Why? Speed and recognition. Saying "question mark" just to type out "?" is slow and could be faulty if the speech recognition software thinks you literally want the words "question mark".
* **Avoid specialized words or names**. Why? So you don't have to specifically train the software to recognize uncommon words like "numpy" (mine thought I said "numb pie"). Workaround/trade-off: you have to spell it out, maybe using the first letters of more common words, like "Neptune unicorn moose panda Yoda" to spell out "numpy". Afterwards, you can reassign "numpy" to a shorter label that uses more common words, like "numb pie" or "pneumatic".
* **"Be polite"**. Each new sentence starts with "please" and roughly marks out a new command/line in the code.

# More Example Code:

Print:

```
Please print this string of words
```
prints out: `this string of words`

Import:

```
Please import test
Please import numpy as nectarine pony
```

Use An Import Module's Function:

```
Please import test
Please use test_function of test
Please use test_function from test
```

Spell it out:

```
Please spell with the first letters of Neptune unicorn moose panda Yoda
```
outputs: `numpy`

Math:

```
Please one plus two
```
outputs: `3`

# Inspirations for Please:

https://github.com/hchiam/programmingByVoice

https://github.com/AnotherTest/-English

https://www.youtube.com/playlist?list=PLBOh8f9FoHHiKx3ZCPxOZWUtZswrj2zI0

# Ideas for Development:

* ~~Try to be able to enter words that are likely to not be trained into Mac Dictation by default (like the word 'numpy'). How? Maybe use some kind of spelling convention, like using the first letters of the words 'Neptune unicorn moose panda Yoda' --> 'numpy'.~~

* ~~Try to map number strings to digits.~~

* ~~Try to import existing python libraries like numpy.~~

* Try variables. Maybe something like 'variable apple' and 'variable apple equals one'. Also: enable remap 'numpy' to 'numb pie'.

* Try embedded expressions. Maybe use "thanks" as a closing bracket of sorts?

* Try in-browser trinket that loads most recent python code from github for you. No installation required.

* Try compiling into C or something so the code can run faster.
