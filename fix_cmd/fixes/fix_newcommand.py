import re

from fix_cmd import fixes, math_parser


FIND_PARAM = re.compile('#([0-9])')


class FindParameters(math_parser.ASTVisitor):
    def __init__(self, container):
        super().__init__(container)

        self.strings = {}

    def find(self, nargs):
        self._start(nargs=nargs)

    def _repl(self, groups, nargs):
        print(groups, nargs)

    def visit_string(self, node, *args, **kwargs):
        """

        :param node: the string
        :type node: fix_cmd.math_parser.String
        """

        node.content = FIND_PARAM.sub(lambda g: self._repl(g, kwargs.get('nargs')), node.content)


class CommandDefinition:
    def __init__(self, command):

        if len(command.parameters) not in [2, 3]:
            raise Exception('\\newcommand prend 2 ou 3 paramètres')

        if not isinstance(command.parameters[0].element.left, math_parser.Command):
            raise Exception('le premier paramètre de \\newcommand devrait commencer par "\\"')

        self.name = command.parameters[0].element.left.name

        self.nargs = 0
        if len(command.parameters) == 3:
            if not command.parameters[1].squared:
                raise Exception('le second paramètre de \\newcommand{{{}}} devrait être [x]'.format(self.name))
            if not isinstance(command.parameters[1].element.left, math_parser.String):
                raise Exception('le second paramètre de \\newcommand{{{}}} n\'est pas un nombre'.format(self.name))
            try:
                self.nargs = int(command.parameters[1].element.left.content)
            except ValueError:
                raise Exception('le second paramètre de \\newcommand{{{}}} n\'est pas un nombre'.format(self.name))

            self.replace_with = command.parameters[2].element
            f = FindParameters(self.replace_with)
            f.find(self.nargs)
        else:
            self.replace_with = command.parameters[1].element

    def replace(self, node):
        """

        :param node: the command
        :type node: fix_cmd.math_parser.Command
        """
        print('use {}'.format(self.name))


class FixNewCommandContext(fixes.FixContext):
    def __init__(self, container):
        super().__init__(container)

        self.commands = {}

    def add_command(self, command):
        """Add a command

        :param command: the command
        :type command: CommandDefinition
        """

        if command.name in self.commands:
            raise Exception('{} défini deux fois'.format(command.name))

        self.commands[command.name] = command


class Applier(math_parser.ASTVisitor):
    def apply(self, context, path):
        """The actual fix

        :param context: the context
        :type context: FixNewCommandContext
        :param path: the file from where the math expression is issued
        :type path: str
        """
        self._start(context=context, path=path)

    def visit_command(self, node, *args, **kwargs):
        """

        :param node: the command
        :type node: fix_cmd.math_parser.Command
        """

        context = kwargs.get('context')
        path = kwargs.get('path')

        if node.name == 'newcommand':
            if len(node.parameters) == 0:
                raise fixes.FixError(path, '\\newcommand\\xxx (style TeX)')

            try:
                context.add_command(CommandDefinition(node))
            except Exception as e:
                raise fixes.FixError(path, str(e))

            math_parser.delete_ast_node(node)

        elif node.name in context.commands:
            try:
                context.commands[node.name].replace(node)
            except Exception as e:
                raise fixes.FixError(path, str(e))
        else:
            super().visit_command(node, *args, **kwargs)


class FixNewCommand(fixes.Fix):
    def create_context(self, container, *args, **kwargs):
        """Context object for a given container

        :param container: the container
        :type container: fix_cmd.content.Container
        """
        return FixNewCommandContext(container)

    def fix(self, math_expr, context, path, *args, **kwargs):
        """The actual fix

        :param context: the context
        :param math_expr: the math expression to fix
        :type math_expr: fix_cmd.fixes.MathExpression
        :param path: the file from where the math expression is issued
        :type path: str
        """
        Applier(math_expr.ast).apply(context=context, path=path)
