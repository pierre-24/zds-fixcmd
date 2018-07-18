from tests import ZdsFixCmdTestCase

from fix_cmd import fix_math, math_parser
from fix_cmd.math_parser import MathToken as T


class MathTestCase(ZdsFixCmdTestCase):

    def test_parsing(self):
        """Test the parsing of a math expression"""

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

        # parser
        m = '\\int_a^{\infty} \\left[\\frac{x}{e^{5x}}\\right]\,dx'
        p = math_parser.MathParser(math_parser.MathLexer(m)).expression()
        self.assertEqual(math_parser.Interpreter(p).interpret(), m)

    def test_latex_custom_command(self):
        """Test LaTeXCustomCommand definition and usage"""

        # from string:
        n = fix_math.LaTeXCustomCommand.from_string('\\newcommand\\test{\\textit}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 0)
        self.assertEqual(n.value, '\\textit')

        self.assertEqual(n.use(), '\\textit')

        n = fix_math.LaTeXCustomCommand.from_string('\\newcommand{\\test}{\\textit}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 0)
        self.assertEqual(n.value, '\\textit')

        self.assertEqual(n.use(), '\\textit')

        n = fix_math.LaTeXCustomCommand.from_string('\\newcommand{\\test}[1]{\\textit{#1}}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 1)
        self.assertEqual(n.value, '\\textit{{{1}}}')

        self.assertEqual(n.use(('test',)), '\\textit{test}')

        n = fix_math.LaTeXCustomCommand.from_string('\\newcommand\\test[1]{\\textit{#1}}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 1)
        self.assertEqual(n.value, '\\textit{{{1}}}')

        self.assertEqual(n.use(('test',)), '\\textit{test}')

        # more tricky:
        n = fix_math.LaTeXCustomCommand.from_string('\\newcommand\\inv[2]{#2, #1}')
        self.assertEqual(n.use(('1', '2')), '2, 1')
