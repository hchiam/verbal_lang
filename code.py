# this is just sample code
print("this string of words")
apple = None
banana = None
apple = 1
print(str(apple))
banana = 300
coconut = 'some words'
dragon_fruit = [ 8 , 9 , 10 , 11 , 12 ]
crazy_list = [ 1 , 2 , 'tree bark' ]
result = 1 + 2
print(str(result))
if True:
	print("this is a 1 line if statement")

if 1 == 1:
	print("this should print")

print("there should be nothing between this line")
if 1 == 2:
	print("it should not print this")

if 1 == 2:
	print("it should ! print this end if")

print("and this line")
circle = [ -1 , 0 , 1 , 2 , 3 ]
for index in circle:
	print(str(index))

# this is a comment
def test(item):
	print(str(item))

other = 'it works'
test(other)
import alternate
from library import test
test.test_function()
test.test_function()
crazy_list = [ 1 , 2 , 'tree bark' ]
sequence = [ 0 , 1 , 2 ]
for item in sequence:
	print(crazy_list[item])

import numpy as numb_pie
array = [ 2 , 3 , 4 ]
print("array is " + str(array))
print("use array of numb pie on " + str(array))
output = numb_pie.array(array)
print("output of array of numb pie is " + str(output))


def fake_fibonacci(number):
	if number == 0:
		return 0
	
	if number == 1:
		return 1
	
	answer_1 = fake_fibonacci(number - 1)
	answer_2 = fake_fibonacci(number - 2)
	return answer_1 + answer_2

output = fake_fibonacci(0)
print("step 1: output = " + str(output))
output = fake_fibonacci(1)
print("step 2: output = " + str(output))
output = fake_fibonacci(2)
print("step 3: output = " + str(output))
output = fake_fibonacci(3)
print("step 4: output = " + str(output))
