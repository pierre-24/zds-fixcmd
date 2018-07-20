from tests import ZdsFixCmdTestCase

from fix_cmd import fixes, math_parser
from fix_cmd.fixes import fix_newcommand, fix_spaces


class FixTestCase(ZdsFixCmdTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = self.copy_to_temporary_directory('article.zip')

    def test_fix(self):
        """Test the principle of the fix class"""

        def replace(math_expr, container, p):
            # change every math expression to $a$ or $$a$$
            math_expr.ast = math_parser.Expression(math_parser.String('a'))

        content = fixes.FixableContent.extract(self.path, fixes=[replace])
        self.assertTrue(replace in content.fixes)
        content.fix()

        self.assertEqual(content.introduction_value.count('$a$'), 0)
        self.assertEqual(content.conclusion_value.count('$a$'), 0)

        self.assertEqual(content.children[0].text_value.count('$$a$$'), 5)
        self.assertEqual(content.children[0].text_value.count('$a$'), 6)

        extract = content.children_dict['principe-physique']
        self.match_expected('fix.principe-physique', extract.text_value)

        self.assertEqual(content.children[1].text_value.count('$$a$$'), 2)
        self.assertEqual(content.children[1].text_value.count('$a$'), 6)

        self.assertEqual(content.children[2].text_value.count('$a$'), 0)
        self.assertEqual(content.children[3].text_value.count('$a$'), 0)

    def test_fix_with_class(self):

        class MyFix(fixes.Fix):
            """Instead of changing the expression, it will simply count"""

            def create_context(self, container, *args, **kwargs):
                c = super().create_context(container, *args, **kwargs)
                c.data = 0
                return c

            def fix(self, math_expr, context, p, *args, **kwargs):
                context.data += 1

        f = MyFix()
        content = fixes.FixableContent.extract(self.path, fixes=[f])
        content.fix()

        self.assertEqual(f.context['naviguer-presque-sans-gps-grace-a-la-navigation-inertielle'].data, 12)


class WithCheck:
    def check_base(self, expr, expected, fix, context):
        m = fixes.MathExpression(expr)
        fix.fix(m, context, 'none')

        self.assertEqual(math_parser.Interpreter(m.ast).interpret(), expected)


class NewCommandTestCase(ZdsFixCmdTestCase, WithCheck):

    def check(self, expr, expected):
        f = fix_newcommand.FixNewCommand()
        context = fix_newcommand.FixNewCommandContext(None)

        self.check_base(expr, expected, f, context)

    def test_base(self):
        """Test the principle"""

        self.check('\\newcommand{\\test}{\\infty}\\test', '\\infty')
        self.check('\\newcommand\\test{\\infty}\\test', '\\infty')
        self.check('\\newcommand{\\test}[1]{\\a{<#1>}{#1}}\\test{x}', '\\a{<x>}{x}')
        self.check('\\newcommand{\\a}[1]{\\u{#1}}\\newcommand{\\b}[1]{\\v{#1}}\\a{x}\\b{y}', '\\u{x}\\v{y}')
        self.check('x\\newcommand{\\a}[1]{\\u{#1}}\\newcommand{\\b}[1]{\\v{#1}}\\a{\\b{y}}', 'x\\u{\\v{y}}')

    def test_fix_article(self):
        """Test the fix on content"""

        path = self.copy_to_temporary_directory('article.zip')

        f = fix_newcommand.FixNewCommand()
        content = fixes.FixableContent.extract(path, fixes=[f])
        content.fix()

        extract = content.children_dict['principe-physique']
        self.match_expected('newcommand.principe-physique', extract.text_value)

    def test_fix_tutorial(self):
        """Test the fix on content"""

        path = self.copy_to_temporary_directory('tuto.zip')

        f = fix_newcommand.FixNewCommand()
        content = fixes.FixableContent.extract(path, fixes=[f])
        content.fix()

        extract = content.children_dict['et-encore-un'].children_dict['du-binaire']
        self.match_expected('newcommand.du-binaire', extract.text_value)

        extract = content.children_dict['test-aussi'].children_dict['une-section-qui-utilise-la-commande']
        self.match_expected('newcommand.une-section-qui-utilise-la-commande', extract.text_value)


class SpacesTestCase(ZdsFixCmdTestCase, WithCheck):

    def check(self, expr, expected, env=True):
        f = fix_spaces.FixSpaces(env)
        context = fixes.FixContext(None)

        self.check_base(expr, expected, f, context)

    def test_base(self):
        """Test the principle"""

        self.check('  ', '')
        self.check(' test ', 'test')
        self.check(' \\vec{a} ', '\\vec{a}')
        self.check(' x\\begin{a}x\\end{a}y ', '\nx\\begin{a}x\\end{a}y\n')
        self.check(' \\begin{a}x\\end{a} ', '\n\\begin{a}x\\end{a}\n')

        self.check(' \\begin{a}x\\end{a} ', '\\begin{a}x\\end{a}', False)  # do not fix envs
