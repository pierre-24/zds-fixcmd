# Note: inspired by https://github.com/zestedesavoir/zds-site/blob/dev/zds/tutorialv2/

import zipfile

try:
    import ujson as json_handler
except ImportError:
    try:
        import simplejson as json_handler
    except ImportError:
        import json as json_handler


class Base:
    title = ''
    slug = ''
    parent = None

    def __init__(self, title, slug='', parent=None):
        self.title = title
        self.slug = slug
        self.parent = parent

    def __str__(self):
        return '{} <{}>'.format(self.__class__, self.title)


class Container(Base):
    """
     A container, which can have sub-Containers or Extracts.
    """

    children = []
    children_dict = {}

    introduction_path = None
    introduction_value = ''
    conclusion_path = None
    conclusion_value = ''

    def __init__(self, title, slug='', parent=None):
        super().__init__(title, slug, parent)

        self.children = []
        self.children_dict = {}

    def top_container(self):
        """
        :return: Top container (for which parent is ``None``)
        :rtype: Content
        """
        current = self
        while current.parent is not None:
            current = current.parent

        return current

    def can_add_children(self, _type=None):
        """

        :param _type: the type of which the children should be
        :type _type: type
        :return: ``True`` if the container contains childre, ``False`` otherwise.
        :rtype: bool
        """

        if len(self.children) == 0:
            return True

        if _type is not None:
            return isinstance(self.children[0], _type)
        else:
            return True

    def add_child(self, child):
        """Add a child

        :param child: the child
        :type child: Container|Extract
        """

        if not self.can_add_children(Extract if type(child) is Extract else Container):
            raise Exception('Impossible d\'ajouter "{}" au conteneur "{}"'.format(child.title, self.title))

        child.parent = self
        self.children.append(child)
        self.children_dict[child.slug] = child


class Extract(Base):
    """
    A content extract from a Container.
    """

    text_path = None
    text_value = ''

    def __init__(self, title, slug='', parent=None):
        super().__init__(title, slug, parent)


class BadArchiveError(Exception):
    pass


class BadManifestError(Exception):
    pass


class Content(Container):

    type = ''
    manifest = ''

    def __init__(self, title, slug=''):
        super().__init__(title, slug, None)

    @staticmethod
    def extract(path):
        """Open a zip file and create a content

        :param path: the path
        :type path: str
        :rtype: Content
        """

        def read_in_zip(archive, path):
            """Read a file in the archive and get text

            :param archive: the zip
            :type archive: zpifile.ZupFile
            :param path: path in the archive
            :type path: str
            :rtype: str
            """

            try:
                txt = str(archive.read(path), 'utf-8')
            except KeyError:
                raise BadArchiveError('Cette archive ne contient pas de fichier "{}".'.format(path))
            except UnicodeDecodeError:
                raise BadArchiveError('L\'encodage de "{}" n\'est pas de l\'UTF-8.'.format(path))

            return txt

        zip_archive = zipfile.ZipFile(path, 'r')

        # is the manifest ok ?
        try:
            manifest = read_in_zip(zip_archive, 'manifest.json')
            manifest = json_handler.loads(manifest)
        except ValueError:
            raise BadArchiveError(
                'Une erreur est survenue durant la lecture du manifest, '
                'vérifiez qu\'il s\'agit de JSON correctement formaté.')
        if 'version' not in manifest or manifest['version'] not in (2, 2.1):
            raise BadManifestError('Ce n\'est pas un manifest issu d\'un contenu récent (v2.x)')

        # extract info
        if 'title' not in manifest:
            raise BadManifestError('Pas de titre dans le manifest')
        if 'slug' not in manifest:
            raise BadManifestError('Pas de slug dans le manifest')

        content = Content(manifest['title'], manifest['slug'])

        if 'type' in manifest:
            content.type = manifest['type']
        else:
            content.type = 'TUTORIAL'

        content.manifest = manifest

        # extract containers and extracts:
        if 'introduction' in manifest:
            content.introduction_path = manifest['introduction']
        if 'conclusion' in manifest:
            content.conclusion_path = manifest['conclusion']

        def fill(json_sub, parent):
            """Create the structure from the manifest

            :param json_sub: subset of the json file
            :type json_sub: dict
            :param parent: parent container
            :type parent: Container
            """
            if 'children' in json_sub:  # it is a container
                for child in json_sub['children']:
                    if 'title' not in child:
                        raise BadManifestError('pas de titre pour enfant dans {}'.format(parent.title))
                    if 'slug' not in child:
                        raise BadManifestError('pas de slug pour enfant dans {}'.format(parent.title))

                    if child['object'] == 'container':
                        c = Container(child['title'], child['slug'])
                        if 'introduction' in child:
                            c.introduction_path = child['introduction']
                        if 'conclusion' in child:
                            c.conclusion_path = child['conclusion']

                        fill(child, c)
                    else:
                        c = Extract(child['title'], child['slug'])
                        if 'text' in child:
                            c.text_path = child['text']

                    parent.add_child(c)

        fill(manifest, content)

        # check if all files are present in the archive, and extract them
        def walk(archive, container):
            """Get all files that the archive should contain

            :param archive: the zip
            :type archive: zpifile.ZupFile
            :param container: the container
            :type container: Container
            """
            if container.introduction_path:
                container.introduction_value = read_in_zip(archive, container.introduction_path)
            if container.conclusion_path:
                container.conclusion_value = read_in_zip(archive, container.conclusion_path)

            for child in container.children:
                if isinstance(child, Container):
                    walk(archive, child)
                else:
                    child.text_value = read_in_zip(archive, child.text_path)

        walk(zip_archive, content)
        return content

    def save(self, path):
        zip_archive = zipfile.ZipFile(path, 'w')

        # dump manifest
        zip_archive.writestr('manifest.json', json_handler.dumps(self.manifest, indent=4, ensure_ascii=False))

        # dump other files
        def walk(archive, container):
            """Get all files that the archive should contain

            :param archive: the zip
            :type archive: zpifile.ZupFile
            :param container: the container
            :type container: Container
            """
            if container.introduction_path:
                zip_archive.writestr(container.introduction_path, container.introduction_value)
            if container.conclusion_path:
                zip_archive.writestr(container.conclusion_path, container.conclusion_value)

            for child in container.children:
                if isinstance(child, Container):
                    walk(archive, child)
                else:
                    zip_archive.writestr(child.text_path, child.text_value)

        walk(zip_archive, self)
        zip_archive.close()
