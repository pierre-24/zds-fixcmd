"""
Simple parser for LaTeX math expression (capture commands and environment).

Grammar:

```
BSLASH := '\' ;
LCB := '{' ;
RCB = '}' ;

word := [a-zA-Z]* ;
not_word :=  [1-9+-*/=:()[]] | SPACE | BSLASH (LCB | RCB) ;
string := (not_word? word)* ;

sub_element := LCB math RCB ;
command := BSLASH word sub_element* ;
environment := BSLASH "begin" subelement* math BSLASH "end" LCB word RCB ;
expression = (string | command | environment | sub_element) math? ;

ast := expression? EOF ;
```

Enough for the current needs.
"""

BSLASH, LCB, RCB, EOF = ('\\', '{', '}', 'EOF')
STRING = 'STRING'
SYMBOL = 'SYMBOL'

SYMBOLS_TR = {
    '\\': BSLASH,
    '{': LCB,
    '}': RCB
}


class MathToken:
    def __init__(self, type_, value, position=-1):
        self.type = type_
        self.value = value
        self.position = position

    def __repr__(self):
        return 'Token({}, {}{})'.format(
            self.type, repr(self.value), ', {}'.format(self.position) if self.position > -1 else '')


class LexerException(Exception):
    def __init__(self, position, msg):
        super().__init__('lexer error at position {}: {}'.format(position, msg))
        self.position = position
        self.message = msg


class MathLexer:
    """Lexer
    """

    def __init__(self, input_):
        self.input = input_
        self.pos = 0
        self.current_string = None
        self.next()

    def next(self):
        """Go to the next token
        """

        if self.pos >= len(self.input):
            self.current_string = None
        else:
            if self.input[self.pos] not in SYMBOLS_TR:
                positions = sorted(a for a in [self.input.find(a, self.pos) for a in SYMBOLS_TR] if a > self.pos)
                if len(positions) == 0:
                    npos = len(self.input)
                else:
                    npos = positions[0]
            else:
                npos = self.pos + 1

            self.current_string = self.input[self.pos:npos]
            self.pos = npos

    def tokenize(self):
        """Tokenize the input
        """

        while self.current_string is not None:
            pos = self.pos
            if self.current_string in SYMBOLS_TR:
                yield MathToken(SYMBOLS_TR[self.current_string], self.current_string, pos - len(self.current_string))
            else:
                yield MathToken(STRING, self.current_string, pos - len(self.current_string))
            self.next()

        yield MathToken(EOF, None, self.pos)


class AST:
    """AST element
    """
    def __init__(self):
        self.parent = None


class String(AST):
    """String

    :param content: the content of the string
    :type content: str
    """
    def __init__(self, content):
        super().__init__()
        self.content = content


class Expression(AST):
    """Math sequence

    :param left: left value
    :type left: String|Command|Environment
    :param right: right value
    :type right: Expression|None
    """

    def __init__(self, left, right=None):
        super().__init__()
        self.left = left
        self.right = right

        self.left.parent = self

        if self.right is not None:
            self.right.parent = self


class SubElement(AST):
    """SubElement

    :param element: the element
    :type element: Expression
    """

    def __init__(self, element):
        super().__init__()
        self.element = element
        self.element.parent = self


class Command(AST):
    """Command

    :param name: name of the command
    :type name: str
    :param parameters: parameters of the command (if any)
    :type parameters: list of SubElement
    """
    def __init__(self, name, parameters):
        super().__init__()
        self.name = name
        self.parameters = parameters

        for p in parameters:
            p.parent = self


class Environment(AST):
    """Environment

    :param name: name of the environment
    :type name: str
    :param parameters: parameters of the command (if any)
    :type parameters: list of SubElement
    :param content: content of the environment
    :type content: Expression
    """
    def __init__(self, name, content, parameters=None):
        super().__init__()
        self.name = name
        self.parameters = parameters if parameters is not None else []
        self.content = content

        self.content.parent = self

        for p in parameters:
            p.parent = self


class ParserException(Exception):
    def __init__(self, token, msg):
        super().__init__('parser error at position {} [{}]: {}'.format(token.position, repr(token), msg))
        self.token = token
        self.message = msg


class MathParser:
    """Parser (generate and AST from the tokens).

    :type lexer: MathLexer
    :param lexer: The lexer
    """

    def __init__(self, lexer):
        self.lexer = lexer
        self.tokenizer = lexer.tokenize()
        self.current_token = None
        self.previous_tokens = []
        self.use_previous = 0
        self.atom_id = 0
        self.next()

    def eat(self, token_type):
        """Consume the token if of the right type

        :param token_type: the token type
        :type token_type: str
        :raise ParserException: if not of the correct type
        """
        if self.current_token.type == token_type:
            self.next()
        else:
            raise ParserException(self.current_token, 'token must be {}'.format(token_type))

    def next(self):
        """Get the next token
        """

        try:
            if self.current_token is not None:
                self.previous_tokens.append(self.current_token)
            self.current_token = next(self.tokenizer)
        except StopIteration:
            self.current_token = MathToken(EOF, None)

    def word(self):
        """Ensure that the current token is a word

        :rtype: str
        """

        if self.current_token.type != STRING:
            raise ParserException(self.current_token, 'expected STRING')

        i = 0
        for c in self.current_token.value:
            if not c.isalpha():
                break
            i += 1

        word = self.current_token.value[0:i + 1]
        self.current_token.value = self.current_token.value[i + 1:]
        self.current_token.position += i

        if word == '':
            raise ParserException(self.current_token, 'empty word')

        return word

    def environment_name(self):
        """

        :rtype: str
        """

        self.eat(LCB)
        node = self.word()

        if self.current_token.value != '':
            raise ParserException(self.current_token, 'environement name is not a word')

        self.eat(RCB)

        return node

    def sub_element(self):
        """element inside curly braces

        :rtype: SubElement
        """

        self.eat(LCB)
        node = self.expression()
        self.eat(RCB)

        return SubElement(node)

    def expression(self):
        """Math

        :rtype: Expression
        """

        if self.current_token.type == STRING:
            left = String(self.current_token.value)
            self.next()
        elif self.current_token.type == LCB:
            left = self.sub_element()
        elif self.current_token.type == BSLASH:
            self.eat(BSLASH)
            if self.current_token.type in [LCB, RCB]:  # it was only escaping
                left = String('\\' + self.current_token.value)
                self.next()
            elif self.current_token.type == STRING:  # it is either an environment or a command, let's see
                name = self.word()

                string_left = self.current_token.value != ''

                is_environment = False
                if name == 'begin':  # yeah, it is an environment
                    if string_left:
                        raise ParserException(self.current_token, 'LCB expected!')

                    is_environment = True
                    name = self.environment_name()

                parameters = []
                if not string_left:
                    self.next()
                    while self.current_token.type == LCB:
                        parameters.append(self.sub_element())

                if not is_environment:
                    left = Command(name, parameters)
                else:
                    content = self.expression()

                    # environment termination (check that it makes sense!)
                    self.eat(BSLASH)
                    w = self.word()
                    if w != 'end':
                        raise ParserException(self.current_token, 'expected "end"')
                    self.eat(LCB)
                    w = self.word()
                    if w != name:
                        raise ParserException(self.current_token, 'beging "{}" but end "{}"'.format(name, w))
                    self.eat(RCB)

                    left = Environment(name, content, parameters)
            else:
                raise ParserException(self.current_token, 'BSLASH not followed by STRING, LCB or RCB')
        else:
            raise ParserException(self.current_token, 'unexpected token')

        right = None
        if self.current_token.type not in [EOF, RCB]:
            right = self.expression()

        return Expression(left=left, right=right)

    def ast(self):
        """

        :rtype: Expression
        """

        node = None

        if self.current_token.type != EOF:
            node = self.expression()

        self.eat(EOF)
        return node


class NodeVisitor(object):
    """Implementation of the visitor pattern. Expect ``visit_[type](node)`` functions, where ``[type]`` is the
    type of the node, **lowercase**.
    """

    def visit(self, node, *args, **kwargs):
        method_name = 'visit_' + type(node).__name__.lower()
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, *args, **kwargs)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__.lower()))


class ASTVisitor(NodeVisitor):
    """Visitor for this AST"""

    def __init__(self, node):
        self.node = node

    def _start(self, *args, **kwargs):
        """Start the visit
        """
        self.visit(self.node, *args, **kwargs)

    def visit_expression(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: Expression
        """

        self.visit(node.left, *args, **kwargs)
        if node.right is not None:
            self.visit(node.right, *args, **kwargs)

    def visit_string(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: String
        """
        pass

    def visit_subelement(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: SubElement
        """

        self.visit(node.element, *args, **kwargs)

    def visit_command(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: Command
        """

        for p in node.parameters:
            self.visit(p, *args, **kwargs)

    def visit_environment(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: Environment
        """

        for p in node.parameters:
            self.visit(p, *args, **kwargs)

        self.visit(node.content, *args, **kwargs)


class Interpreter(NodeVisitor):
    """Give a string representation (the LaTeX code) of the AST

    :param node: the node
    :type node: Expression
    """

    def __init__(self, node):
        self.node = node

    def interpret(self):
        """

        :rtype: str
        """
        return self.visit(self.node)

    def visit_expression(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: Expression
        :rtype: str
        """

        r = self.visit(node.left, *args, **kwargs)
        if node.right is not None:
            r += self.visit(node.right, *args, **kwargs)

        return r

    def visit_string(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: String
        :rtype: str
        """

        return node.content

    def visit_subelement(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: SubElement
        """

        return LCB + self.visit(node.element, *args, **kwargs) + RCB

    def visit_command(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: Command
        :rtype: str
        """

        r = BSLASH + node.name

        for p in node.parameters:
            r += self.visit(p, *args, **kwargs)

        return r

    def visit_environment(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: Environment
        :rtype: str
        """

        r = BSLASH + 'begin' + LCB + node.name + RCB

        for p in node.parameters:
            r += self.visit(p, *args, **kwargs)

        r += self.visit(node.content, *args, **kwargs)

        return r + LCB + 'end' + RCB
