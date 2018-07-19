from tests import ZdsFixCmdTestCase

from fix_cmd import fixes, math_parser


class FixTestCase(ZdsFixCmdTestCase):

    def test_fix(self):
        path = self.copy_to_temporary_directory('article.zip')
        content = fixes.FixableContent.extract(path)

        def replace(math_expr, container, p):
            math_expr.ast = math_parser.Expression(math_parser.String('a'))  # change every math expression into $a$

        content.fixes = [replace]
        content.fix_containers()

        self.assertEqual(content.introduction_value.count('$a$'), 0)
        self.assertEqual(content.children[0].text_value.count('$$a$$'), 5)

        self.assertEqual(content.children[1].text_value.count('$$a$$'), 2)
        self.assertEqual(content.children[1].text_value.count('$a$'), 6)
