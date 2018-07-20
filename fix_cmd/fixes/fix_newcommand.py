import re
import copy

from fix_cmd import fixes, math_parser


FIND_PARAM = re.compile('#([0-9])')


class NCError(Exception):
    def __init__(self, cmd, err):
        super().__init__('\\{}: {}'.format(cmd, err))


class ReplaceParameters(math_parser.ASTVisitor):
    def __init__(self, container):
        super().__init__(container)

    def replace(self, cmd, args):
        self._start(cmd=cmd, args=args)

    def visit_string(self, node, *args, **kwargs):
        """

        :param node: the string
        :type node: fix_cmd.math_parser.String
        """

        p = node.parent
        right = p.right
        splits = []
        content = node.content
        args = kwargs.get('args')
        cmd = kwargs.get('cmd')

        b = 0
        found = False
        for i in FIND_PARAM.finditer(node.content):
            if int(i.group(1)) > len(args):
                raise NCError(cmd, '{} args expected, but #{}'.format(len(args), i.group(1)))
            found = True
            n = i.span()[0]
            if n - b > 0:
                splits.append(b)
            splits.append(n)
            b = n + 2

        if b != len(content):
            splits.append(b)

        splits.append(len(content))

        if found:
            for i in range(len(splits) - 1):
                b, e = splits[i:i + 2]
                if content[b] == '#':
                    new_node = copy.deepcopy(args[int(content[b + 1]) - 1])
                else:
                    new_node = math_parser.String(content[b:e])
                if b != 0:
                    p.right = math_parser.Expression(new_node, right)
                    p.right.parent = p
                    p = p.right
                else:
                    p.left = new_node
                    new_node.parent = p


class CommandDefinition:
    def __init__(self, command):

        if len(command.parameters) not in [2, 3]:
            raise NCError('newcommand', '2 or 3 parameters expected')

        if not isinstance(command.parameters[0].element.left, math_parser.Command):
            raise NCError('newcommand', 'first parameter should start with "\\"')

        self.name = command.parameters[0].element.left.name

        self.nargs = 0
        if len(command.parameters) == 3:
            if not command.parameters[1].squared:
                raise NCError(
                    'newcommand\\{}'.format(self.name), 'second parameter should be between square parentheses')
            if not isinstance(command.parameters[1].element.left, math_parser.String):
                raise NCError('newcommand\\{}'.format(self.name), 'second parameter should be int')
            try:
                self.nargs = int(command.parameters[1].element.left.content)
            except ValueError:
                raise NCError('newcommand\\{}'.format(self.name), 'second parameter is not int'.format(self.name))

            self.replace_with = command.parameters[2].element
        else:
            self.replace_with = command.parameters[1].element

    def _copy_and_replace(self, args):
        """Copy the AST and replace arguments by their value

        :param args: the arguments
        :type args: list of fix_cmd.math_parser.Expression
        :rtype: fix_cmd.math_parser.Expression
        """

        n = copy.deepcopy(self.replace_with)
        ReplaceParameters(n).replace(self.name, args)

        return n

    def replace(self, node):
        """

        :param node: the command
        :type node: fix_cmd.math_parser.Command
        """

        if len(node.parameters) != self.nargs:
            raise NCError(
                self.name,
                '{} parameter(s), but {} expected'.format(len(node.parameters), self.nargs))

        n = self._copy_and_replace([x.element for x in node.parameters])

        end = n
        while end.right is not None:
            end = end.right

        parent = node.parent
        math_parser.replace_ast_node(parent, n)


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
            raise NCError(command.name, 'defined twice')

        self.commands[command.name] = command


class Applier(math_parser.ASTVisitor):
    def __init__(self, node):
        super().__init__(node)

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

        parent = node.parent

        if node.name == 'newcommand':
            if len(node.parameters) == 0:
                raise fixes.FixError(path, '\\newcommand\\xxx (TeX style)')

            try:
                context.add_command(CommandDefinition(node))
            except NCError as e:
                raise fixes.FixError(path, str(e))

            math_parser.delete_ast_node(node)
            self.visit(parent.left, *args, **kwargs)  # need to visit the new node that takes the place of the command

        elif node.name in context.commands:
            try:
                context.commands[node.name].replace(node)
            except NCError as e:
                raise fixes.FixError(path, str(e))
            self.visit(parent.left, *args, **kwargs)  # ... same here
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
