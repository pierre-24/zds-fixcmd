from tests import ZdsFixCmdTestCase

from fix_cmd import fix_math


class MathTestCase(ZdsFixCmdTestCase):
    def test_newcommand(self):

        # from string:
        n = fix_math.LaTeXCommand.from_string('\\newcommand\\test{\\textit}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 0)
        self.assertEqual(n.value, '\\textit')

        self.assertEqual(n.use(), '\\textit')

        n = fix_math.LaTeXCommand.from_string('\\newcommand{\\test}{\\textit}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 0)
        self.assertEqual(n.value, '\\textit')

        self.assertEqual(n.use(), '\\textit')

        n = fix_math.LaTeXCommand.from_string('\\newcommand{\\test}[1]{\\textit{#1}}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 1)
        self.assertEqual(n.value, '\\textit{{{1}}}')

        self.assertEqual(n.use(('test',)), '\\textit{test}')

        n = fix_math.LaTeXCommand.from_string('\\newcommand\\test[1]{\\textit{#1}}')
        self.assertEqual(n.name, '\\test')
        self.assertEqual(n.nargs, 1)
        self.assertEqual(n.value, '\\textit{{{1}}}')

        self.assertEqual(n.use(('test',)), '\\textit{test}')
