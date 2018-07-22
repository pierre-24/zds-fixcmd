"""
Change "align" environment by "aligned"
"""

from fix_cmd import fixes, math_parser


class AlignError(Exception):
    def __init__(self, cmd, err):
        super().__init__('\\{}: {}'.format(cmd, err))


class ChangeEnv(math_parser.ASTVisitor):
    def change(self):
        self._start()

    def visit_environment(self, node, *args, **kwargs):
        if node.name == 'align':
            node.name = 'aligned'


class FixAlign(fixes.Fix):

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

        ChangeEnv(math_expr.ast).change()
