import re

from fix_cmd import content, math_parser

FIND_MATH = re.compile('\\$(\\$)?(.*?)(\\$)?\\$', re.DOTALL)


class MathExpression:
    def __init__(self, expression, line=True):
        self.base_expression = expression
        self.ast = math_parser.MathParser.parse(expression)
        self.line = line


class FixError(Exception):
    def __init__(self, path, err):
        super().__init__('{}: {}'.format(path, err))


def dummy(math_expr, container, path, *args, **kwargs):
    """Fix a math expression found in a container

    :param math_expr: the math expression to fix
    :type math_expr: fix_cmd.fixes.MathExpression
    :param container: the container
    :type container: fix_cmd.content.Container
    :param path: the file from where the math expression is issued
    :type path: str
    """

    pass


class FixableContent(content.Content):

    def __init__(self, title, slug, fixes=None):
        super().__init__(title, slug)

        self.fixes = fixes if fixes is not None else [dummy]

    def walk_containers(self, container=None):
        """Walk the different containers

        :param container: the container to explore
        :type container: fix_cmd.content.Container
        """
        if container is None:
            container = self

        yield container

        if len(container.children) != 0 and isinstance(container.children[0], content.Container):
            for child in container.children:
                for _y in self.walk_containers(child):
                    yield _y

    def fix(self, *args, **kwargs):
        """Fix the different containers
        """

        for container in self.walk_containers():
            self.fix_container(container, *args, **kwargs)

    def fix_container(self, container, *args, **kwargs):
        """Fix a given container

        :param container: the container
        :type container: fix_cmd.content.Container
        """

        if container.introduction_path is not None:
            container.introduction_value = FIND_MATH.sub(
                lambda g: self._fix_math(g, container, container.introduction_path, *args, **kwargs),
                container.introduction_value)

        if len(container.children) != 0 and isinstance(container.children[0], content.Extract):
            for child in container.children:
                child.text_value = FIND_MATH.sub(
                    lambda g: self._fix_math(g, container, child.text_path, *args, **kwargs),
                    child.text_value)

        if container.conclusion_path is not None:
            container.conclusion_value = FIND_MATH.sub(
                lambda g: self._fix_math(g, container, container.conclusion_path, *args, **kwargs),
                container.conclusion_value)

    def _fix_math(self, groups, container, path, *args, **kwargs):
        """Fix a math expression found in a container

        :param container: the container
        :type container: fix_cmd.content.Container
        :param path: the file from where the math expression is issued
        :type path: str
        :rtype: str
        """

        if groups.group(1) != groups.group(3):
            raise FixError(
                path, 'begin and end of math expression are not the same (${}!=${})'.format(
                    groups.group(1), groups.group(3)))

        e = MathExpression(groups.group(2), line=groups.group(1) == '')

        for fix in self.fixes:
            fix(e, container, path, *args, **kwargs)

        sep = '$' * (1 if groups.group(1) is None else 2)
        s = math_parser.Interpreter(e.ast).interpret()

        if s != '':
            return sep + math_parser.Interpreter(e.ast).interpret() + sep
        else:
            return ''  # remove empty math

    @staticmethod
    def extract(path, fixes=None):
        """Extract a content

        :param path: the path
        :type path: str
        :param fixes: the fixes to apply
        :type fixes: list
        :rtype: FixableContent
        """
        x = content.Content.extract(path)

        y = FixableContent(x.title, x.slug, fixes=fixes)
        y.type = x.type
        y.manifest = x.manifest
        y.children = x.children
        y.children_dict = x.children_dict

        return y


class FixContext:
    """Basic context"""

    def __init__(self, container):
        self.container = container
        self.data = None


class Fix:
    """A fix.

    The context is container based.
    """
    def __init__(self):
        self.context = {}

    def create_context(self, container, *args, **kwargs):
        """Context object for a given container

        :param container: the container
        :type container: fix_cmd.content.Container
        :rtype: FixContext
        """

        return FixContext(container)

    def fix(self, math_expr, context, path, *args, **kwargs):
        """The actual fix

        :param context: the context
        :param math_expr: the math expression to fix
        :type math_expr: fix_cmd.fixes.MathExpression
        :param path: the file from where the math expression is issued
        :type path: str
        """
        raise NotImplementedError()

    def __call__(self, math_expr, container, path, *args, **kwargs):
        """

        :param obj: the content
        :type obj: fix_cmd.fixes.FixableContent
        :param math_expr: the math expression to fix
        :type math_expr: fix_cmd.fixes.MathExpression
        :param container: the container
        :type container: fix_cmd.content.Container
        :param path: the file from where the math expression is issued
        :type path: str
        """

        if container.slug not in self.context:
            self.context[container.slug] = self.create_context(container, *args, **kwargs)

        context = self.context[container.slug]
        return self.fix(math_expr, context, path, *args, **kwargs)
