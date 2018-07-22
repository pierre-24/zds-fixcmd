"""
Strip spaces at the beginning and the end of the math expressions, but add "\\n" if an environment is found.
"""

from fix_cmd import fixes, math_parser


class SpacesError(Exception):
    def __init__(self, cmd, err):
        super().__init__('\\{}: {}'.format(cmd, err))


class FindEnv(math_parser.ASTVisitor):
    def __init__(self, node):
        super().__init__(node)
        self.found = False

    def find(self):
        self._start()
        return self.found

    def visit_environment(self, node, *args, **kwargs):
        self.found = True


class FixSpaces(fixes.Fix):

    def __init__(self, fix_environments=True):
        super().__init__()
        self.fix_environments = fix_environments

    def fix(self, math_expr, context, path, *args, **kwargs):
        """The actual fix

        :param context: the context
        :param math_expr: the math expression to fix
        :type math_expr: fix_cmd.fixes.MathExpression
        :param path: the file from where the math expression is issued
        :type path: str
        """

        start = math_expr.ast

        while True:
            if not isinstance(start.left, math_parser.String):
                break

            if start.left.content[0].isspace():
                striped = start.left.content.lstrip()

                if striped == '':
                    math_parser.delete_ast_node(start)
                else:
                    start.left.content = striped
                    break
            else:
                break

        end = start
        while end.right is not None:
            end = end.right

        while True:
            parent = end.parent

            if not isinstance(end.left, math_parser.String):
                break

            if end.left.content[-1].isspace():
                striped = end.left.content.rstrip()

                if striped == '':
                    math_parser.delete_ast_node(end)
                    end = parent
                else:
                    end.left.content = striped
                    break
            else:
                break

        if self.fix_environments and FindEnv(start).find():
            if isinstance(start.left, math_parser.String):
                start.left.content = '\n' + start.left.content
            else:
                e = math_parser.Expression(start.left, start.right)
                start.left = math_parser.String('\n')
                start.right = e
                e.parent = start
                if id(end) == id(start):
                    end = e
            if isinstance(end.left, math_parser.String):
                end.left.content += '\n'
            else:
                end.right = math_parser.Expression(math_parser.String('\n'))
                end.right.parent = end
