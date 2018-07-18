import re


class BadCommand(Exception):
    def __init__(self, cmd, err):
        super().__init__('Erreur dans "{}": {}'.format(cmd, err))


FIND_ARGS = re.compile('#([0-9])')


class LaTeXCommand:
    def __init__(self, name, nargs, value):
        self.name = name
        self.nargs = nargs
        self.value = value

    def __str__(self):
        return 'command {} [{}]: {}'.format(self.name, self.nargs, self.value)

    @staticmethod
    def from_string(s):
        """Create an object from the LaTeX definition

        :param s: definition
        :type s: str
        :rtype: LaTeXCommand
        """
        if s[:11] != '\\newcommand':
            raise BadCommand(s, 'ce n\'est pas une définition')

        if s[11] == '{':
            end = s.find('}', 12)
            if end < 12:
                raise BadCommand(s, 'pas de fin au nom')

            name = s[12:end]
            end += 1
        else:
            end1 = s.find('{', 11)
            end2 = s.find('[', 11)

            if end1 < 11 and end2 < 11:
                raise BadCommand(s, 'pas de fin au nom')

            end = end1 if end2 < 11 or end2 > end1 else end2
            name = s[11:end]

        if name == '' or name == '\\':
            raise BadCommand(s, 'la commande n\'a pas de nom')

        nargs = 0
        if s[end] == '[':
            n_end = s.find(']', end)
            if n_end < end:
                raise BadCommand(s, 'pas de fin au nombre d\'arguments')
            try:
                nargs = int(s[end + 1:n_end])
            except ValueError:
                raise BadCommand(s, 'le nombre d\'argument n\'est pas un nombre')

            end = n_end + 1

        if s[-1] != '}':
            raise BadCommand(s, 'la commande n\'a pas de fin')

        value = s[end + 1:-1]
        if value == '':
            raise BadCommand(s, 'la commande n\'a pas de valeur')

        # treat value
        value = value.replace('{', '{{').replace('}', '}}')
        value = FIND_ARGS.sub(lambda g: '{{{}}}'.format(g.group(1)), value)

        return LaTeXCommand(name, nargs, value)

    def use(self, args=()):
        """Use the command and replace by its value

        :param args: the args
        :type args: tuple
        :rtype: str
        """
        if len(args) != self.nargs:
            raise ValueError('le nombre d\'argument ne correspond pas à la définition')

        return self.value.format('', *args)
