"""
Rolling
Version 1.0 (released 2016-01-09)
Direct all comments, suggestions, etc. at /u/the-nick-of-time
Released under the GNU General Public License version 2, as detailed within
the file LICENSE included in the same directory as this code.

This module provides the framework for evaluating roll expressions. Basically,
it adds the capability to parse the operators 'd', 'h', and 'l'.The important
thing to note is that these are simply new binary operators.
The definitions of these operators are as follows:
xdy rolls x y-sided dice and returns a sorted list of these rolls.
    xd[a,b,c,...] rolls x dice with sides a,b,c....
xdyhz rolls x y-sided dice and returns the z highest of these rolls. This
    enables the advantage mechanic.
xdylz rolls x y-sided dice and returns the z lowest of these rolls. This
    enables the disadvantage mechanic.

Any string that can be parsed by this code is called throughout all my related
code a "rollable string". These are similar to arithmetic expressions, just with the above operators added.
Examples of rollable strings:
+4                  (positive four)
-2                  (negative two)
1d6                 (roll a six-sided die with sides numbered one through six)
-1d6                (roll a d6 and take the negative)
3d6+2               (roll 3d6 and add 2 to the sum)
1d6+1d4+1           (roll a d6, add to it a d4, and add one to that)
2d20h1+3+2          (roll 2d20, take the higher of the two rolls, add a total of five to it)
3d6/2               (roll 3d6, divide the sum by 2; note that this returns an unrounded number)
Less applicable functionalities:
1d6^2               (roll a d6, square the result)
1d6^1d4             (roll a d6, raise it to a random power between 1 and 4)
1d4d4d4             (roll a d4, roll that many d4s, sum them and roll that many d4s)
1d[0,0,0,1,1,2]     (roll a six-sided die with three sides being 0, two 1, and one 2)
1d[.5,.33,.25,.20]  (roll a four-sided die with sides 0.5, 0.33, 0.25, and 0.2)
1d100>11            (roll a d100 and check whether the roll is greater than 11; returns a 1 for true and 0 for false)
3d4%5               (roll 3d4, return the remainder after division by 5)

"""

import random

__all__ = ['roll', 'call']


class operator:
    def __init__(self, op, precedence, order):
        self.op = op
        self.precedence = precedence
        self.order = order
        
    def __gt__(self, other):
        return self.precedence > other.precedence
        
    def __ge__(self, other):
        return self.precedence >= other.precedence
        
    def __eq__(self, other):
        return self.op == other

def roll(s, modifiers=0, option='execute'):
    """Roll dice and do arithmetic."""
    global digits, operators
    digits = '0123456789'

    operators = (operator('d', 7, 2),
                 operator('h', 6, 2),
                 operator('l', 6, 2),
                 operator('^', 5, 2),
                 operator('m', 4, 1),
                 operator('p', 4, 1),
                 operator('*', 3, 2),
                 operator('/', 3, 2),
                 operator('-', 2, 2),
                 operator('+', 2, 2),
                 operator('>', 1, 2),
                 operator('<', 1, 2),
                 operator('=', 1, 2))
    if (not isinstance(s, str)):
        # If you're naughty and pass a number in...
        # it really doesn't matter.
        return s + modifiers
    elif (s == ''):
        return 0 + modifiers
    elif (option == 'execute'):
        return (execute(tokens(s)) + modifiers)
    elif (option == 'max'):
        #T=[('*' if item=='d' else item) for item in tokens(s)]
        T = tokens(s)
        for (i, item) in enumerate(T):
            if (item == 'd'):
                if (len(T) >= i + 3 and (T[i + 2] == 'h' or T[i + 2] == 'l')):
                    T[i - 1:i + 4] = [T[i + 3], '*', T[i + 1]]
                else:
                    T[i] = '*'
        return execute(T)
    elif (option == 'critical'):
        T = tokens(s)
        for i in range(len(T)):
            if (T[i] == 'd'):
                T[i - 1] *= 2
        return (execute(T) + modifiers)
    elif (option == 'average'):
        return (execute(tokens(s), av=True) + modifiers)
    elif (option == 'zero'):
        return 0
    #elif (option == 'multipass'):
    #    return displayMultipass(multipass(tokens(s), modifiers))
    elif (option == 'tokenize'):
        return tokens(s)


call = roll  # A hacky workaround for backwards compatibility

def tokens(s):
    """Split a string into tokens for use with execute()"""
    number = []
    operator = []
    out = []
    i = 0
    numflag = s[0] in digits
    opflag = s[0] in operators
    while (i < len(s)):
        char = s[i]
        if (char in digits):
            if (opflag):
                out.extend(operator)
                operator = []
                numflag = not numflag
                opflag = not opflag
            number.append(char)
        elif (char in operators or char == '(' or char == ')'):
            if (numflag):
                out.append(int(''.join(number)))
                number = []
                numflag = not numflag
                opflag = not opflag
            if(char == '+' and (i == 0 or s[i-1] in operators)):
                out.append('p')
            elif(char == '-' and (i == 0 or s[i-1] in operators)):
                out.append('m')
            else:
                operator.append(char)
        elif (char == '['):
            sidelist = []
            while (s[i] != ']'):
                sidelist.append(s[i])
                i += 1
            i += 1
            sidelist.append(s[i])
            out.append(readList(''.join(sidelist)))
        elif (char == 'F'):
            out.append([-1, 0, 1])
        i += 1
    if (numflag):
        out.append(int(''.join(number)))
    elif (opflag):
        out.append(''.join(operator))
    return out


def readList(s, mode='float'):
    """Read a list defined in a string."""
    if (mode == 'float'):
        return list(eval(s))
    elif (mode == 'int'):
        a = list(eval(s))
        for (i, item) in enumerate(a):
            a[i] = int(item)
        return a


def rollBasic(number, sides):
    """Roll a single set of dice."""
    #Returns a sorted (ascending) list of all the numbers rolled
    result = []
    rollList = []
    if (type(sides) is int):
        rollList = list(range(1, sides + 1))
    elif (type(sides) is list):
        rollList = sides
    for all in range(number):
        result.append(rollList[random.randint(0, len(rollList) - 1)])
    result.sort()
    return result


def evaluate(nums, op, av=False):
    """Evaluate expressions."""
    if (op in 'd^*/%+-><='):
        #collapse any lists in preparation for operation
        try:
            nums[0] = sum(nums[0])
        except (TypeError):
            pass

    if (op in 'hl^*/%+-><=&|'):
        try:
            nums[1] = sum(nums[1])
        except (TypeError):
            pass

    if (op == 'd'):
        if (av):
            if (type(nums[1]) is list):
                return (sum(nums[1]) * nums[0]) // len(nums[1])
            else:
                return (1 + nums[1]) * nums[0] // 2
        else:
            return rollBasic(nums[0], nums[1])
    elif (op == 'h'):
        return nums[0][-nums[1]:]
    elif (op == 'l'):
        return nums[0][:nums[1]]
    elif (op == '^'):
        return nums[0]**nums[1]
    elif (op == '*'):
        return nums[0] * nums[1]
    elif (op == '/'):
        return nums[0] / nums[1]
    elif (op == '%'):
        return nums[0] % nums[1]
    elif (op == '+'):
        return nums[0] + nums[1]
    elif (op == '-'):
        return nums[0] - nums[1]
    elif (op == '>'):
        return nums[0] > nums[1]
    elif (op == '<'):
        return nums[0] < nums[1]
    elif (op == '='):
        return nums[0] == nums[1]
    elif (op == '&'):
        return nums[0] and nums[1]
    elif (op == '|'):
        return nums[0] or nums[1]


def unary(num, op):
    """Evaluate unary expressions."""
    try:
        num = sum(num)
    except (TypeError):
        pass
    if (op == 'm'):
        return -num
    elif (op == 'p'):
        return num


def execute(T, av=False):
    """Calculate a result from a list of tokens."""
    oper = []
    nums = []
    while (len(T) > 0):
        current = T.pop(0)
        if (type(current) is int or type(current) is list):
            nums.append(current)
        elif (current == '('):
            oper.append(current)
        elif (current == ')'):
            while (oper[-1] != '('):
                #Evaluate all extant expressions down to the open paren
                if (order(oper[-1]) == 2):
                    nums.append(evaluate(
                        [nums.pop(-2), nums.pop()], oper.pop(), av))
                else:
                    nums.append(unary(nums.pop(), oper.pop()))
            oper.pop()  #Get rid of that last open paren
        elif (current in operators):
            try:
                while (oper[-1] >= current):
                    #check precedence; lower index=higher precedence
                    #perform operation
                    if (order(oper[-1]) == 2):
                        nums.append(evaluate(
                            [nums.pop(-2), nums.pop()], oper.pop(), av))
                    else:
                        nums.append(unary(nums.pop(), oper.pop()))
            except (IndexError):
                pass
            oper.append(current)
            #or add a higher-precedence operator to the stack
    while (len(oper) > 0):
        #empty the operator stack
        if (order(oper[-1]) == 2):
            nums.append(evaluate([nums.pop(-2), nums.pop()], oper.pop(), av))
        else:
            nums.append(unary(nums.pop(), oper.pop()))
    try:
        #collapse list of rolls if able
        nums[0] = sum(nums[0])
    except (TypeError):
        pass
    return sum(nums)

def order(op):
    """Determine the order of an operator."""
    for this in operators:
        if (this == op):
            return this.order
    raise NotFoundError('Operator not valid')

def multipass(T, modifiers=0):
    # note: this does not yet support parentheses
    passes = ["d", "hl", "^mp*/%+-", "><=&|"]
    for run in passes:
        for op in run:
            while (T.count(op)):
                loc = T.index(op)
                if (order[operators.index(op)] == 2):
                    val = evaluate([T[loc - 1], T[loc + 1]], op)
                    T[loc - 1:loc + 2] = [val]
                    #this assignment only works when RHS is iterable
                else:
                    val = unary(T[loc + 1], op)
                    T[loc:loc + 2] = [val]
            out.extend(['+' if modifiers >= 0 else '', modifiers])
        out.append(T)
    out.append(T[0])
    # out should be of the form
    # [[rolls have been made],
    # [selected rolls have been discarded],
    # [arithmetic but not boolean operators have been evaluated],
    # final result]
    return out


def displayMultipass(l):
    out = ['', '', '', '']
    for (i, sec) in enumerate(l):
        for token in sec:
            out[i] += str(token)
        out[i] += '\n'
    return out

    
class NotFoundError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg
