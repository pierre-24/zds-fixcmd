from tests import ZdsFixCmdTestCase

from fix_cmd import fixes, math_parser
from fix_cmd.fixes import fix_newcommand


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
        content.fix_containers()

        self.assertEqual(content.introduction_value.count('$a$'), 0)
        self.assertEqual(content.conclusion_value.count('$a$'), 0)

        self.assertEqual(content.children[0].text_value.count('$$a$$'), 5)
        self.assertEqual(content.children[0].text_value.count('$a$'), 6)

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
        content.fix_containers()

        self.assertEqual(f.context['naviguer-presque-sans-gps-grace-a-la-navigation-inertielle'].data, 12)


class NewCommandTestCase(ZdsFixCmdTestCase):
    def test_base(self):
        """Test the principle"""

        text = '\\newcommand{\\test}[1]{\\a{#1}}\\test{x}'
        context = fix_newcommand.FixNewCommandContext(None)
        m = fixes.MathExpression(text)

        f = fix_newcommand.FixNewCommand()
        f.fix(m, context, 'none')

        print(math_parser.Interpreter(m.ast).interpret())

    def test_fix(self):
        """Test the fix on content"""

        path = self.copy_to_temporary_directory('article.zip')

        f = fix_newcommand.FixNewCommand()
        content = fixes.FixableContent.extract(path, fixes=[f])
        content.fix_containers()
