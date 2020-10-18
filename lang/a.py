
from .dsssss import Stack



## validating token functions

def isString(token):
    return token.startswith('"') and token.endswith('"')


def isInt(token):
    if not token:
        return False
    if token[0] == '-':
        token = token[1:]
    for char in token:
        if not char in ('0','1','2','3','4','5','6','7','8','9',):
            return False
    return True



## evaluator definition

SEPS = {
    ' ', '\n', '\r', ';', '{', '}'
}

_GLOBAL = 0x10

_STR_TYPE = 0x101
_INT_TYPE = 0x102
_FUNC_TYPE = 0x100

_NO_SUCH_VAL = 0x4040404




SYNTAX_KEYWORDS = {
    'setv', 'speak', 'wait', 'unsetv', 'loop', 'endloop', 'that', 'to', 'step', '_res'
}

OPERATORS = {
    '+', '-', '*', '/', '=', '+=', r'\+', '-=', r'\-', '*=', r'\*', r'/=', r'\/'
    '>', '<', '>=', '<=', 
}

OPERATORS_ASSIGNMENT = {'='}

OPERATORS_ASSIGNMENT_MUT = {
    '+', '+=', r'\+', '-', '-=', r'\-', '*', '*=', r'\*'
}

RESERVED_KWS = SYNTAX_KEYWORDS.union(OPERATORS)

___FUNC_TRANSLATION = {
}





class Variable:
    'the structure to store a script session variable'
    def __init__(self, var_name, var_val, var_type):
        self.var_name = var_name
        self.var_val = var_val
        self.var_type = var_type


def variableNameValid(name):
    return (name not in RESERVED_KWS) and ('"' not in name) and ("'" not in name)


class RepeatedClause:
    def __init__(self, block, range_or_cnt):
        self.block = block
        self.count = len(range_or_cnt) if isinstance(range_or_cnt, range) else range_or_cnt


class EvalGrammar:
    
    def __init__(self, string, externalFunctions={
        'speak': print,
        'wait': print,
    }):
        'parse the string into tokens and creates required pre-defined variables.'
        self._keywords = Stack()
        tempKw = Stack()
        isInString: bool = False
        for char in string + '\n':
            if char == '"':
                isInString = not isInString
            if not char in SEPS or isInString:
                tempKw.push(char)
            else:
                kw: str = ''.join(tempKw.items)
                if not kw == '':
                    self._keywords.push(kw)
                tempKw.clear()
        self._keywords.items.reverse()
        
        self._variables = {
            _GLOBAL: []
        }
        for k, v in externalFunctions.items():
            self._variables[_GLOBAL].append(Variable(
                k, v, _FUNC_TYPE
            ))
        
        self._procedures = []
        self._externals = externalFunctions
    

    @staticmethod
    def _findsIndexForVal(lst, var_name):
        'locates the index of a variable name in the given variable list'
        for variable in lst:
            if variable.var_name == var_name:
                return lst.index(variable)
        return _NO_SUCH_VAL
    

    def _findsIndexValOrThrowError(self, var_name):
        'asserted version of _findsIndexForVal'
        if var_name in RESERVED_KWS:
            raise SyntaxError(f'invalid variable name for {var_name}.')
        linkedPos: int = self._findsIndexForVal(self._variables[_GLOBAL], var_name)
        if linkedPos == _NO_SUCH_VAL:
            raise ValueError(f'{var_name} is not defined.')
        return linkedPos
    

    def _referenceVal(self, referenced):
        '''returns the pointer to variable name in the given variable list 
        or reports error if there is none'''
        return self._variables[_GLOBAL][self._findsIndexValOrThrowError(referenced)]
    

    def _assignsVarByLiteral(self, var_name, var_val, var_type):
        '''assigns the variable to the variable list if it is given by plain form
        ,\n\nlike: `setv var_name = var_val` where var_val is a string literal etc
        '''
        # first checks whether this variable exists, if it exists, remove it later
        # removal is experiemental
        indx: int = self._findsIndexForVal(self._variables[_GLOBAL], var_name)
        if var_type == _STR_TYPE:
            self._variables[_GLOBAL].append(Variable(
                var_name, var_val, _STR_TYPE
            ))
        elif var_type == _INT_TYPE:
            self._variables[_GLOBAL].append(Variable(
                var_name, int(var_val), _INT_TYPE
            ))
        if not indx == _NO_SUCH_VAL:
            del self._variables[_GLOBAL][indx]


    def _assignsVarByAnotherVar(self, name: str, referenced: str):
        '''assigns the variable to the variable list if it is given by another variable (name)
        ,\n\nlike: `setv name = referenced`
        '''
        linkedPos: int = self._findsIndexValOrThrowError(referenced)
        # same as above function to remove existing variable
        indx: int = self._findsIndexForVal(self._variables[_GLOBAL], name)
        self._variables[_GLOBAL].append(Variable(
            name, self._variables[_GLOBAL][linkedPos].var_val, 
            self._variables[_GLOBAL][linkedPos].var_type
        ))
        if not indx == _NO_SUCH_VAL:
            del self._variables[_GLOBAL][indx]
    

    def _mutateVal_Add(self, added, referenced: str, op: str):
        '''reassigns the variable with name [referenced] in the given role:\n\n
        for example,
        `setv x - 2` computes x - 2 and assigns it to `x`\n\n
        `setv x \- 2` computes 2 - x and assigns it to `x`.\n\n
        the param [added] is literal. [op] is the operator in place of the above "-"
        '''
        if isinstance(added, str):
            added = added[1:-1]
        
        associativity = 'l' if op[0] == '\\' else 'r'
        
        def fn(a, r):
            if op in ('+', '+=', r'\+'):
                if (isinstance(a, int) and isinstance(r, int)) or \
                    (isinstance(a, str) and isinstance(r, str)):
                    return a + r
                else:
                    return str(a) + str(r)
            elif op in ('-', '-=', r'\-'):
                if isinstance(a, int) and isinstance(r, int):
                    return a - r
                else:
                    raise SyntaxError('"-" operator not allowed in non-number operations.')
            elif op in ('*', '*=', r'\*'):
                if isinstance(a, int) and isinstance(r, int):
                    return a * r
                elif isinstance(a, str) and isinstance(r, str):
                    raise SyntaxError('"*" operator not allowed in non-number operations.')
                else:
                    return r * a
        
        linkedPos: int = self._findsIndexValOrThrowError(referenced)
        if associativity == 'r':
            self._variables[_GLOBAL][linkedPos].var_val = fn(
                self._variables[_GLOBAL][linkedPos].var_val, added
            )
        else:
            self._variables[_GLOBAL][linkedPos].var_val = fn(
                added, self._variables[_GLOBAL][linkedPos].var_val
            )
    

    def _handlesSetv(self):
        '''handles assignments like `setv var_name [op] var_value`
        '''
        assignmts: set = OPERATORS_ASSIGNMENT.union(OPERATORS_ASSIGNMENT_MUT)
        try:
            shouldBeVarName: str = self._keywords.pop()
            if not variableNameValid(shouldBeVarName):
                raise SyntaxError(f'invalid variable name for {shouldBeVarName}.')
            shouldBeAssignation: str = self._keywords.pop()
            if not shouldBeAssignation in assignmts:
                raise SyntaxError(f'Expects a "=" or "+" after {shouldBeVarName}.')
            shouldBeVarVal: str = self._keywords.pop()
            if not isString(shouldBeVarVal):
                pass
        except IndexError:
            raise EOFError(f'Unexpected end of sequence for assignment of {shouldBeVarName}.')
        if isString(shouldBeVarVal):
            stringTypedVal: str = shouldBeVarVal[1:-1]
            if shouldBeAssignation in OPERATORS_ASSIGNMENT:
                self._assignsVarByLiteral(shouldBeVarName, stringTypedVal, _STR_TYPE)
            elif shouldBeAssignation in OPERATORS_ASSIGNMENT_MUT:
                self._mutateVal_Add(
                    shouldBeVarVal, shouldBeVarName, shouldBeAssignation
                )
            
        elif isInt(shouldBeVarVal):
            if shouldBeAssignation in OPERATORS_ASSIGNMENT:
                self._assignsVarByLiteral(shouldBeVarName, shouldBeVarVal, _INT_TYPE)
            elif shouldBeAssignation in OPERATORS_ASSIGNMENT_MUT:
                self._mutateVal_Add(
                    int(shouldBeVarVal), shouldBeVarName, shouldBeAssignation
            )

        else: # it is a referenced variable
            if shouldBeAssignation == '=':
                self._assignsVarByAnotherVar(shouldBeVarName, shouldBeVarVal)
            elif shouldBeAssignation in OPERATORS_ASSIGNMENT_MUT:
                self._mutateVal_Add(
                    self._referenceVal(shouldBeVarVal).var_val, shouldBeVarName, shouldBeAssignation
                )
    

    def _handlesLoop(self):
        '''handles loops like 
        ```
        loop setv i = 0 to 10 step 2 that
            [code]
        endloop
        ```
        where `step` is optional.\n
        this feature is in baby state. it has maximum loop depth (2) and times (999)'''
        # just copies the code block x times... will improve if possible
        loopContent = Stack()
        #intAssignment = Stack()
        loopCount: int = 1
        try:
            shouldBeSetv: str = self._keywords.pop()
            if not shouldBeSetv == 'setv':
                raise SyntaxError('Should set a variable inside loop assignment')

            shouldBeVarName: str = self._keywords.pop()
            if not variableNameValid(shouldBeVarName):
                raise SyntaxError(f'Invalid variable name for {shouldBeVarName}.')

            shouldBeAssignation: str = self._keywords.pop()
            if not shouldBeAssignation == '=':
                raise SyntaxError(f'Expects a "=" after {shouldBeVarName}.')

            shouldBeStartVal: str = self._keywords.pop()
            if not isInt(shouldBeStartVal):
                shouldBeStartVal = self._referenceVal(shouldBeStartVal).var_val
            shouldBeStartVal: int = int(shouldBeStartVal)
            if shouldBeStartVal < 0:
                raise ValueError('"loop" does not allow assignment smaller than 0.')

            shouldBeTo: str = self._keywords.pop()
            if not shouldBeTo == 'to':
                raise SyntaxError(f'Expects a "to" after {shouldBeVarName} = {shouldBeStartVal}.')

            shouldBeEndVal: str = self._keywords.pop()
            if not isInt(shouldBeEndVal):
                shouldBeEndVal = self._referenceVal(shouldBeEndVal).var_val
            shouldBeEndVal: int = int(shouldBeEndVal)
            if shouldBeEndVal > 999:
                raise PermissionError('"loop" does not allow assignment greater than 999 in your role.')

            shouldBeThat: str = self._keywords.pop()
            shouldBeStepLength: int = 1
            if not shouldBeThat == 'that':

                if shouldBeThat == 'step':
                    shouldBeStepLength = self._keywords.pop()
                    if not isInt(shouldBeStepLength):
                        shouldBeStepLength = self._referenceVal(shouldBeStepLength).var_val
                    shouldBeStepLength = int(shouldBeStepLength)
                    if shouldBeStepLength < 0 or shouldBeStepLength > 999:
                        raise PermissionError('"loop" does not allow assignment greater than 999 in your role.')

                    if not self._keywords.pop() == 'that':
                        raise SyntaxError(f'Expects a "that" in closing "loop".')
                else:
                    raise SyntaxError(f'Expects a "that" in closing "loop".')
        except IndexError:
            raise EOFError(f'Unexpected end of sequence.')
        except ValueError:
            raise ValueError (f'Expects integers in the loop assignment.')

        self._assignsVarByLiteral(shouldBeVarName, shouldBeStartVal-shouldBeStepLength, _INT_TYPE)
        loopContent.push('setv')
        loopContent.push(shouldBeVarName)
        loopContent.push('+')
        loopContent.push(str(shouldBeStepLength))
        try:
            while True:
                current = self._keywords.pop()
                if not isString(current):
                    if current == 'loop':
                        loopCount += 1
                        # does not allow two many nests
                        if loopCount == 3:
                            raise PermissionError('You do not have permission to use that many nested loops.')
                    if current == 'endloop':
                        loopCount -= 1
                        if loopCount == 0:
                            break
                    # forbids mutating index
                    if not isString(current) and (current in ('setv', 'unsetv') and self._keywords.peek() == shouldBeVarName):
                        raise SyntaxError('Mutating a loop index variable is not permitted.')
                loopContent.push(current)
        except IndexError:
            raise EOFError(f'Unexpected end of sequence.')
        self._keywords.push(RepeatedClause(loopContent, range(shouldBeStartVal, shouldBeEndVal, shouldBeStepLength)))


    def _handlesRemove(self):
        '''deletes the variable from the variable list and thus is invisible from the script.\n\n
        `unsetv x` removes variable `x`
        '''
        try:
            shouldBeVarName: str = self._keywords.pop()
        except IndexError:
            raise EOFError(f'Unexpected end of sequence for deletion of {shouldBeVarName}.')
        if not variableNameValid(shouldBeVarName):
            raise SyntaxError(f'invalid variable name for {shouldBeVarName}.')
        del self._variables[_GLOBAL][self._findsIndexValOrThrowError(shouldBeVarName)]


    def _handlesSpeak(self):
        '''adds the external function named "speak" with spplied string to the event queue.\n\n
        like: `speak "hello world"` will execute nonebot `session.send("hello world")` if
        in the supplied externalFunctions there is:
        ```
        externalFunctions = {
            'speak' = lambda s: asyncio.get_event_loop().run_until_complete(nonebotSession.send(s)),
            ...
        }
        ```
        '''
        try:
            shouldBeVar: str = self._keywords.pop()
        except IndexError:
            raise EOFError('Unexpected end of sequence of "speak".')
        if not isString(shouldBeVar):
            if self._findsIndexForVal(self._variables[_GLOBAL], shouldBeVar) == _NO_SUCH_VAL:
                raise ValueError(f'{shouldBeVar} is not defined.')
            if shouldBeVar in self._externals:
                raise ValueError('No, you can\'t do that.')
        self._procedures.append(
            'speak(str(' + shouldBeVar + '))'
        )


    def _handlesWait(self):
        'handles function `wait` in a similar way to _handlesSpeak'
        try:
            shouldBeTime: str = self._keywords.pop()
        except IndexError:
            raise EOFError('Unexpected end of sequence of "wait".')
        if not isInt(shouldBeTime):
            if isString(shouldBeTime):
                raise ValueError('Unexpected token after "wait".')
            if self._findsIndexForVal(self._variables[_GLOBAL], shouldBeTime) == _NO_SUCH_VAL:
                raise ValueError(f'{shouldBeTime} is not defined.')
        self._procedures.append(
            'wait(' + shouldBeTime + ')'
        )


    def _handlesRepeatedClause(self, clause):
        self._keywords.push(RepeatedClause(clause.block, clause.count - 1))
        for tk in reversed(clause.block.items):
            self._keywords.push(tk)

    def _scan(self):
        'scans for operations from above to bottom.'
        while not self._keywords.is_empty():
            token = self._keywords.pop()
            if token in SEPS:
                continue
            elif token == 'setv':
                self._handlesSetv()
            elif token == 'unsetv':
                self._handlesRemove()
            elif token == 'loop':
                self._handlesLoop()
            elif token == 'speak':
                self._handlesSpeak()
            elif token == 'wait':
                self._handlesWait()
            elif isinstance(token, RepeatedClause):
                if token.count > 0:
                    self._handlesRepeatedClause(token)
            # consider this, at default, a defined variable (todo)
            else:
                raise SyntaxError(f'Unexpected token {token}.')
            self._exec_so_far()


    def _exec_so_far(self):
        'runs the first event in the event queue.'
        varz: dict = dict()
        for each in self._variables[_GLOBAL]:
            varz[each.var_name] = each.var_val
        if len(self._procedures):
            exec(self._procedures[0], varz)
            del self._procedures[0]


    def exec_in_global(self):
        'runs the code!'
        self._scan()

