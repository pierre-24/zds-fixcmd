"""
Simple parser for LaTeX math expression (capture commands).

Grammar:

```
BSLASH := '\' ;
LCB := '{' ;
RCB := '}' ;
LSB := '[' ;
RSB := ']' ;
DOWN := '_' ;
UP := '^' ;

escaped_char := BSLASH (BSLASH | LCB | LSB) ;
char_m := (CHAR \ { BSLASH | LCB | RCB | UP | DOWN }) | escaped ;
word := [a-zA-Z]* ;
string := char_m* ;

spaces := ',' | '!' | '>' | ';' | ':' ;

sub_element := LCB expression RCB ;
squared_parameter := LSB expression RSB ;

command := BSLASH ((word (sub_element | squared_parameter)*) | spaces) ;
unary_operator := (DOWN | UP) ol_expression ;

ol_expression := char_m | command | sub_element ;
expression := (string | command | sub_element) expression? ;

ast := expression? EOF ;
```

Environments are detected latter on.
"""

BSLASH, LCB, RCB, LSB, RSB, DOWN, UP, EOF = ('\\', '{', '}', '[', ']', '_', '^', 'EOF')
STRING = 'STRING'
SYMBOL = 'SYMBOL'

SPACES = [',', '!', '>', ';', ':']

SYMBOLS_TR = {
    '\\': BSLASH,
    '{': LCB,
    '}': RCB,
    '[': LSB,
    ']': RSB,
    '_': DOWN,
    '^': UP
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


class Empty(AST):
    pass


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
    :param squared: LSB instead of LCB
    :type squared: bool
    """

    def __init__(self, element, squared=False):
        super().__init__()
        self.element = element
        self.squared = squared
        self.element.parent = self


class UnaryOperator(AST):
    """Unary operator

    :param element: the element
    :type element: SubElement|Command|String
    :param operator: the operator
    :type operator: str
    """

    def __init__(self, operator, element):
        super().__init__()
        self.operator = operator
        self.element = element
        self.element.parent = self


class Command(AST):
    """Command

    :param name: name of the command
    :type name: str
    :param parameters: parameters of the command (if any)
    :type parameters: list of SubElement
    """
    def __init__(self, name, parameters=None):
        super().__init__()
        self.name = name
        self.parameters = parameters if parameters is not None else []

        for p in self.parameters:
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


class NodeVisitor(object):
    """Implementation of the visitor pattern.
    Expect ``visit_[type](node)`` functions, where ``[type]`` is the type of the node, **lowercased**.
    """

    def visit(self, node, *args, **kwargs):
        method_name = 'visit_' + type(node).__name__.lower()
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        raise Exception('No visit_{} method'.format(type(node).__name__.lower()))


class ASTVisitor(NodeVisitor):
    """Visitor for this AST

    :param node: the node to visit
    :type node: AST
    """

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

    def visit_unaryoperator(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: UnaryOperator
        """

        self.visit(node.element, *args, **kwargs)

    def visit_empty(self, node, *args, **kwargs):
        pass


class BadEnvironment(Exception):
    pass


class EnvironmentFix(ASTVisitor):
    def __init__(self, node):
        super().__init__(node)

        self.commands = []

    def modify(self):
        self.commands = []
        self._start(depth=0)

        # check if the order make sense, then change for env
        env_stack = []
        for name, obj, state, depth in self.commands:
            if state == 'begin':
                env_stack.append((name, obj, depth))
            else:
                if env_stack[-1][0] != name:
                    raise BadEnvironment('environment "{}" closed before "{}"'.format(name, env_stack[-1]))

                if depth != env_stack[-1][2]:
                    raise BadEnvironment('environment "{}" is not closed in the right context'.format(name))

                begin = env_stack[-1][1]
                end = obj

                # ok, let's rewire that
                begin_parent = begin.parent
                end_parent = end.parent
                end_grandparent = end_parent.parent

                e = Environment(name, begin_parent.right, parameters=begin.parameters[1:])
                e.parent = begin_parent

                begin_parent.left = e
                begin_parent.right = end_parent.right

                if end_parent.right is not None:
                    begin_parent.right.parent = begin_parent

                end_grandparent.right = None

                del env_stack[-1]

        if len(env_stack) != 0:
            raise BadEnvironment('env {} not closed'.format(', '.join(a[0] for a in env_stack)))

        return self.node

    def visit_command(self, node, *args, **kwargs):
        """Detect begin and end of environments

        :param node: node
        :type node: Command
        """
        if node.name in ['begin', 'end']:
            if len(node.parameters) == 0:
                raise BadEnvironment('\\begin but no name')
            sub = node.parameters[0].element
            if not isinstance(sub.left, String):
                raise BadEnvironment('name of env is more complex than a word: {}'.format(
                    Interpreter(sub.left).interpret()))

            name = sub.left.content
            for c in name:
                if not c.isalpha() and c != '*':
                    raise BadEnvironment('{} is not a valid name'.format(name))

            self.commands.append((name, node, node.name, kwargs.get('depth')))

        kwargs['depth'] = kwargs.get('depth') + 1
        super().visit_command(node, *args, **kwargs)

    def visit_subelement(self, node, *args, **kwargs):
        """Rewritten to increase depth each type a subelement is visited

        :param node: node
        :type node: SubElement
        """

        kwargs['depth'] = kwargs.get('depth') + 1
        super().visit_subelement(node, *args, **kwargs)


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

    def one_char(self):
        """get only one char

        :return:
        """

        if self.current_token.type != STRING:
            raise ParserException(self.current_token, 'expected STRING in one_char')

        c = self.current_token.value[0]
        self.current_token.value = self.current_token.value[1:]
        self.current_token.position += 1

        if self.current_token.value == '':
            self.next()

        return c

    def word(self):
        """Ensure that the current token is a word

        :rtype: str
        """

        if self.current_token.type != STRING:
            raise ParserException(self.current_token, 'expected STRING in word')

        i = 0
        for c in self.current_token.value:
            if not c.isalpha():
                break
            i += 1

        word = self.current_token.value[0:i]
        self.current_token.value = self.current_token.value[i:]
        self.current_token.position += i

        if word == '':
            raise ParserException(self.current_token, 'empty word')

        if self.current_token.value == '':
            self.next()

        return word

    def squared_parameter(self):
        """element inside squared brackets

        :rtype: SubElement
        """

        self.eat(LSB)
        node = self.expression(additional_stoppers=[RSB])
        self.eat(RSB)

        return SubElement(node, squared=True)

    def sub_element(self):
        """element inside curly braces

        :rtype: SubElement
        """

        self.eat(LCB)
        node = self.expression(additional_stoppers=[RCB])
        self.eat(RCB)

        return SubElement(node)

    def unary_operator(self):
        """Unary operator

        :rtype: UnaryOperator
        """

        operator = self.current_token.value
        self.next()

        if self.current_token.type == STRING:  # only catch the first character
            content = String(self.one_char())
        elif self.current_token.type == LCB:
            content = self.sub_element()
        elif self.current_token.type == BSLASH:
            content = self.command_or_escaped()
        else:
            raise ParserException(self.current_token, 'expected STRING, LCB or BSLASH in unary operator')

        return UnaryOperator(operator, content)

    def command_or_escaped(self):
        """

        :rtype: Command|String
        """

        self.eat(BSLASH)

        if self.current_token.type in [BSLASH, LCB, RCB]:  # it was only escaping
            node = String('\\' + self.current_token.value)
            self.next()
        elif self.current_token.type == STRING:  # command
            parameters = []
            if self.current_token.value[0] in SPACES:  # it is a space command
                name = self.one_char()
            else:
                name = self.word()
                while self.current_token.type in [LCB, LSB]:
                    if self.current_token.type == LCB:
                        parameters.append(self.sub_element())
                    else:
                        parameters.append(self.squared_parameter())
            node = Command(name, parameters)
        else:
            raise ParserException(self.current_token, 'BSLASH not followed by STRING, LCB or RCB')

        return node

    def expression(self, additional_stoppers=None):
        """Math

        :param additional_stoppers: stop right search (if sub element context)
        :type additional_stoppers: list
        :rtype: Expression
        """

        if self.current_token.type == STRING:
            left = String(self.current_token.value)
            self.next()
        elif self.current_token.type == LCB:
            left = self.sub_element()
        elif self.current_token.type in [LSB, RSB]:  # here, it is nothing more than a string
            left = String(self.current_token.value)
            self.next()
        elif self.current_token.type in [UP, DOWN]:
            left = self.unary_operator()
        elif self.current_token.type == BSLASH:
            left = self.command_or_escaped()
        else:
            raise ParserException(self.current_token, 'unexpected token')

        right = None
        stop = [EOF]
        if additional_stoppers:
            stop.extend(additional_stoppers)

        if self.current_token.type not in stop:
            right = self.expression(additional_stoppers=additional_stoppers)

            # merge strings that follow each other
            while isinstance(left, String) and right is not None and isinstance(right.left, String):
                left.content += right.left.content
                right = right.right

        return Expression(left=left, right=right)

    def ast(self, environments=True):
        """

        :param environments: post-modify AST to get the environments
        :type environments: bool
        :rtype: Expression
        """

        node = None

        if self.current_token.type != EOF:
            node = self.expression()
            if environments:
                EnvironmentFix(node).modify()

        self.eat(EOF)
        return node

    @staticmethod
    def parse(s, environments=True):
        """Parse a string

        :param environments: post-modify AST to get the environments
        :type environments: bool
        :param s: string
        :type s: str
        :rtype: Expression
        """
        return MathParser(MathLexer(s)).ast(environments)


class Interpreter(NodeVisitor):
    """Give a string representation (the LaTeX code) of the AST

    :param node: the node
    :type node: AST
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

        return (LSB if node.squared else LCB) + \
            self.visit(node.element, *args, **kwargs) + \
            (RSB if node.squared else RCB)

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
        return r + BSLASH + 'end' + LCB + node.name + RCB

    def visit_unaryoperator(self, node, *args, **kwargs):
        """

        :param node: node
        :type node: UnaryOperator
        :rtype: str
        """

        return node.operator + self.visit(node.element, *args, **kwargs)

    def visit_empty(self, node, *args, **kwargs):
        return ''


def delete_ast_node(node):
    """
    If deletion of node "n":

    A          A
    |\         |\
    a \        a \
       N    →     N (N remains!)
       |\         |\
       n \        c \
          C          D
          |\
          c \    (if A)
             D

    :param node: node to delete
    :type node: AST
    """

    if isinstance(node, Expression):
        N = node
        C = node.right
    else:
        N = node.parent
        C = N.right

    if C is not None:
        N.left = C.left
        N.left.parent = N
        N.right = C.right
        if N.right is not None:
            N.right.parent = N
    else:  # then B will only contain an empty()
        N.left = Empty()
        N.left.parent = N


def replace_ast_node(node, other):
    """
    If insertion of X  instead of N
                    |\            |
                    x \           n
                       Y
                       |
                       y

    A          A
    |\         |\
    a \        a \
       N    →     N   (N remains!)
       |\         |\
       n \        x \
          C          Y
                     |\
                     y \
                        C

    :param node: node to delete
    :type node: AST
    :param other: node insert instead
    :type other: AST
    """

    if isinstance(node, Expression) and isinstance(other, Expression):
        N = node
        C = node.right
        X = other
        Y = other

        while Y.right is not None:
            Y = Y.right

        N.left = X.left
        N.left.parent = N
        N.right = X.right
        if N.right is not None:
            N.right.parent = N
        if id(X) == id(Y):
            Y = N

        if C is not None:
            Y.right = C
            Y.right.parent = Y

    elif not isinstance(node, Expression) and not isinstance(other, Expression):
        parent = node.parent
        parent.left = other
        other.parent = parent
    else:
        raise Exception('?')
