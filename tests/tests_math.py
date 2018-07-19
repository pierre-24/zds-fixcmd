from tests import ZdsFixCmdTestCase

from fix_cmd import math_parser
from fix_cmd.math_parser import MathToken as T


class MathTestCase(ZdsFixCmdTestCase):

    def test_lexer(self):
        """Test the lexing of a math expression"""

        # Lexer
        tests_lexer = [
            ('1+1', [T(math_parser.STRING, '1+1')]),
            ('1-\\frac{a}{b}', [
                T(math_parser.STRING, '1-'),
                T(math_parser.BSLASH, '\\'),
                T(math_parser.STRING, 'frac'),
                T(math_parser.LCB, '{'),
                T(math_parser.STRING, 'a'),
                T(math_parser.RCB, '}'),
                T(math_parser.LCB, '{'),
                T(math_parser.STRING, 'b'),
                T(math_parser.RCB, '}')
            ]),
            ('a=||\\vec{b}||+ 1', [
                T(math_parser.STRING, 'a=||'),
                T(math_parser.BSLASH, '\\'),
                T(math_parser.STRING, 'vec'),
                T(math_parser.LCB, '{'),
                T(math_parser.STRING, 'b'),
                T(math_parser.RCB, '}'),
                T(math_parser.STRING, '||+ 1')
            ]),
            ('\\int_a^b x\\,dx', [
                T(math_parser.BSLASH, '\\'),
                T(math_parser.STRING, 'int'),
                T(math_parser.DOWN, '_'),
                T(math_parser.STRING, 'a'),
                T(math_parser.UP, '^'),
                T(math_parser.STRING, 'b x'),
                T(math_parser.BSLASH, '\\'),
                T(math_parser.STRING, ',dx'),
            ])
        ]

        for s, r in tests_lexer:
            lexer = math_parser.MathLexer(s)
            lexed = [i for i in lexer.tokenize()]
            self.assertEqual(len(lexed) - 1, len(r))
            for i, token in enumerate(r):
                self.assertEqual(token.type, lexed[i].type, msg='{} of {}'.format(i, s))
                self.assertEqual(token.value, lexed[i].value, msg='{} of {}'.format(i, s))

            self.assertEqual(lexed[-1].type, math_parser.EOF)

    def test_parser(self):
        """Test the parsing of a math expression"""

        # base
        m = '\\int_{a}^\\infty\\frac{1}{x}\\,dx'
        ast = math_parser.MathParser(math_parser.MathLexer(m)).ast()
        self.assertEqual(m, math_parser.Interpreter(ast).interpret())

        t = ast
        self.assertEqual(type(t.left), math_parser.Command)
        self.assertEqual(t.left.name, 'int')
        self.assertEqual(len(t.left.parameters), 0)

        t = t.right
        self.assertEqual(type(t.left), math_parser.UnaryOperator)
        self.assertEqual(t.left.operator, '_')
        self.assertEqual(type(t.left.element), math_parser.SubElement)
        self.assertEqual(type(t.left.element.element), math_parser.Expression)
        self.assertEqual(type(t.left.element.element.left), math_parser.String)
        self.assertEqual(t.left.element.element.left.content, 'a')

        t = t.right
        self.assertEqual(type(t.left), math_parser.UnaryOperator)
        self.assertEqual(t.left.operator, '^')
        self.assertEqual(type(t.left.element), math_parser.Command)
        self.assertEqual(t.left.element.name, 'infty')
        self.assertEqual(len(t.left.element.parameters), 0)

        t = t.right
        self.assertEqual(type(t.left), math_parser.Command)
        self.assertEqual(t.left.name, 'frac')
        self.assertEqual(len(t.left.parameters), 2)
        self.assertTrue(all(type(a) is math_parser.SubElement for a in t.left.parameters))
        self.assertTrue(all(type(a.element) is math_parser.Expression for a in t.left.parameters))
        self.assertTrue(all(type(a.element.left) is math_parser.String for a in t.left.parameters))
        self.assertEqual(t.left.parameters[0].element.left.content, '1')
        self.assertEqual(t.left.parameters[1].element.left.content, 'x')

        t = t.right
        self.assertEqual(type(t.left), math_parser.Command)
        self.assertEqual(t.left.name, ',')
        self.assertEqual(len(t.left.parameters), 0)

        t = t.right
        self.assertEqual(type(t.left), math_parser.String)
        self.assertEqual(t.left.content, 'dx')

        self.assertIsNone(t.right)

        # environments
        m = '\\begin{a}[1]\\begin{b}[2]\\begin{c}x\\end{c}\\end{b}\\begin{c}y\\end{c}\\end{a}'
        ast = math_parser.MathParser(math_parser.MathLexer(m)).ast()
        self.assertEqual(m, math_parser.Interpreter(ast).interpret())

        t = ast
        self.assertEqual(type(t.left), math_parser.Environment)
        self.assertEqual(t.left.name, 'a')
        self.assertEqual(len(t.left.parameters), 1)
        self.assertEqual(t.left.parameters[0].element.left.content, '1')

        self.assertIsNone(t.right)

        t = t.left.content
        self.assertEqual(type(t.left), math_parser.Environment)
        self.assertEqual(t.left.name, 'b')
        self.assertEqual(len(t.left.parameters), 1)
        self.assertEqual(t.left.parameters[0].element.left.content, '2')

        x = t.left.content
        self.assertEqual(type(x.left), math_parser.Environment)
        self.assertEqual(x.left.name, 'c')
        self.assertEqual(len(x.left.parameters), 0)
        self.assertEqual(x.left.content.left.content, 'x')

        t = t.right
        self.assertEqual(type(t.left), math_parser.Environment)
        self.assertEqual(t.left.name, 'c')
        self.assertEqual(len(t.left.parameters), 0)
        self.assertEqual(t.left.content.left.content, 'y')

        # imbrication
        m = '\\begin{a}{\\begin{b}x\\end{b}}y\\end{a}'
        ast = math_parser.MathParser(math_parser.MathLexer(m)).ast()
        self.assertEqual(m, math_parser.Interpreter(ast).interpret())

        t = ast
        self.assertEqual(type(t.left), math_parser.Environment)
        self.assertEqual(t.left.name, 'a')
        self.assertEqual(len(t.left.parameters), 1)

        x = t.left.parameters[0].element
        self.assertEqual(type(x.left), math_parser.Environment)
        self.assertEqual(x.left.name, 'b')
        self.assertEqual(len(x.left.parameters), 0)

        x = t.left.content
        self.assertEqual(type(x.left), math_parser.String)
        self.assertEqual(x.left.content, 'y')

        self.assertIsNone(t.right)
