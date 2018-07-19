import re

from fix_cmd import content, math_parser

FIND_MATH = re.compile('\\$(\\$)?(.*?)(\\$)?\\$', re.DOTALL)


class MathExpression:
    def __init__(self, expression, line=True):
        self.base_expression = expression
        self.ast = math_parser.MathParser(math_parser.MathLexer(expression)).ast()
        self.line = line


class FixError(Exception):
    pass


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

    fixes = [
        dummy,
    ]

    def __init__(self, title, slug):
        super().__init__(title, slug)

        self.data = {}

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

    def fix_containers(self, *args, **kwargs):
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
                'Le début et la fin de l\'expression ne correspondent pas dans {}'.format(path))

        e = MathExpression(groups.group(2), line=groups.group(1) == '')

        for fix in self.fixes:
            fix(e, container, path, *args, **kwargs)

        sep = '$' * (1 if groups.group(1) is None else 2)
        return sep + math_parser.Interpreter(e.ast).interpret() + sep

    @staticmethod
    def extract(path):
        """Extract a content

        :param path: the path
        :type path: str
        :rtype: FixableContent
        """
        x = content.Content.extract(path)

        y = FixableContent(x.title, x.slug)
        y.type = x.type
        y.manifest = x.manifest
        y.children = x.children
        y.children_dict = x.children_dict

        return y
