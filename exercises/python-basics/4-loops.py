"""Loops"""

"""While loop"""

# A while-loop is a control flow statement for specifying iteration, which allows code to be executed repeatedly.

# TODO: Write a while loop that prints break_condition and increments it, until it reaches 5

break_condition = 0

while break_condition < 9:
    print(break_condition)
    break_condition += 1

print("out of while loop")

# ----------------------------------------------

"""For loop"""

# For-loop is a control flow statement for specifying iteration, which allows code to be executed repeatedly.

# TODO: Iterate over pets, printing each one

pets = ["dog", "cat", "horse", "rabbit", "snake"]

for pet in pets:
    print(pet)

# Create a list containing the numbers 0 through 4.
numbers = list(range(5))
for number in numbers:
    print(number)

# A nested loop is a loop inside another loop. For each row, the inner loop
# visits every column, so this prints all six row-column pairs.
for row in range(3):
    for column in range(2):
        print(f"row={row}, column={column}")
