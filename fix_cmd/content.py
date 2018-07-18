# Note: inspired by https://github.com/zestedesavoir/zds-site/blob/dev/zds/tutorialv2/

import os
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

    introduction = None
    conclusion = None

    def __init__(self, title, slug='', parent=None):
        super().__init__(title, slug, parent)

        self.children = []
        self.children_dict = {}

    def get_path(self):
        """Get the physical path to the container.

        :return: physical path
        :rtype: str
        """

        base = ''
        if self.parent:
            base = self.parent.get_path()

        return os.path.join(base, self.slug)

    def top_container(self):
        """
        :return: Top container (for which parent is ``None``)
        :rtype: Content
        """
        current = self
        while current.parent is not None:
            current = current.parent

        return current

    def has_children(self, _type=None):
        """

        :param _type: the type of which the children should be
        :type _type: type
        :return: ``True`` if the container contains childre, ``False`` otherwise.
        :rtype: bool
        """

        if len(self.children) == 0:
            return False

        if _type is not None:
            return isinstance(self.children[0], _type)
        else:
            return True

    def add_child(self, child):
        """Add a child

        :param child: the child
        :type child: Container|Extract
        """

        if self.has_children(Extract if child is Extract else Container):
            raise Exception('Impossible d\'ajouter {} au conteneur {}'.format(child.title, self.title))

        child.parent = self
        self.children.append(child)
        self.children_dict[child.slug] = child

    def get_introduction(self):
        if self.introduction:
            return self.top_container()._read(self.introduction)
        else:
            return None

    def get_conclusion(self):
        if self.conclusion:
            return self.top_container()._read(self.conclusion)
        else:
            return None


class Extract(Base):
    """
    A content extract from a Container.
    """

    text = None

    def __init__(self, title, slug='', parent=None):
        super().__init__(title, slug, parent)

    def get_path(self):
        """
        Get the physical path to the extract.

        :return: physical path
        :rtype: str
        """

        return os.path.join(self.parent.get_path(), self.slug) + '.md'

    def get_text(self):
        """Get the text of the extract

        :rtype: str
        """

        return self.parent.top_container()._read(self.text)

    def update_text(self, new_text):
        """Update the text in the extract

        :param new_text: the new extract text
        :type new_text: str
        """

        return self.parent.top_container()._write(self.text, new_text)


class BadArchiveError(Exception):
    pass


class BadManifestError(Exception):
    pass


class Content(Container):

    type = ''

    manifest = ''
    archive = None

    def __init__(self, path):
        super().__init__('', '')
        self.open(path)

    def open(self, path):
        """Open a zip file and create a content

            :param path: the path
            :type path: str
            :rtype: Content
            """

        zip_archive = zipfile.ZipFile(path, 'a')

        # is the manifest ok ?
        try:
            manifest = str(zip_archive.read('manifest.json'), 'utf-8')
            manifest = json_handler.loads(manifest)
        except KeyError:
            raise BadArchiveError('Cette archive ne contient pas de fichier manifest.json.')
        except UnicodeDecodeError:
            raise BadArchiveError('L\'encodage du manifest.json n\'est pas de l\'UTF-8.')
        except ValueError:
            raise BadArchiveError(
                'Une erreur est survenue durant la lecture du manifest, '
                'vérifiez qu\'il s\'agit de JSON correctement formaté.')
        if 'version' not in manifest or manifest['version'] not in (2, 2.1):
            raise BadManifestError('Ce n\'est pas un manifest d\'un contenu récent (v2)')

        # extract infos
        self.slug = manifest['slug']
        self.title = manifest['title']

        if 'type' in manifest:
            self.type = manifest['type']
        else:
            self.type = 'TUTORIAL'

        self.manifest = manifest

        # extract containers and extracts:
        if 'introduction' in manifest:
            self.introduction = manifest['introduction']
        if 'conclusion' in manifest:
            self.conclusion = manifest['conclusion']

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
                            c.introduction = child['introduction']
                        if 'conclusion' in child:
                            c.conclusion = child['conclusion']

                        fill(child, c)
                    else:
                        c = Extract(child['title'], child['slug'])
                        if 'text' in child:
                            c.text = child['text']

                    parent.add_child(c)

        fill(manifest, self)

        # check if all files are present in the archive
        def walk(container):
            """Get all files that the archive should contain

            :param container: the container
            :type container: Container
            """
            if container.introduction:
                yield container.introduction
            if container.conclusion:
                yield container.conclusion

            for child in container.children:
                if isinstance(child, Container):
                    for _y in walk(child):
                        yield _y
                else:
                    yield child.text

        for f in walk(self):
            try:
                zip_archive.getinfo(f)
            except KeyError:
                BadArchiveError('Le fichier {} n\'existe pas dans l\'archive'.format(f))

        self.archive = zip_archive

    def close(self):
        self.archive.close()
        self.archive = None

    def _read(self, path):
        """Read a file in the archive and get text

        :param path: path in the archive
        :type path: str
        :rtype: str
        """
        if self.archive is None:
            raise IOError('closed')

        try:
            txt = str(self.archive.read(path), 'utf-8')
        except KeyError:
            raise BadArchiveError('Cette archive ne contient pas de fichier {}.'.format(path))
        except UnicodeDecodeError:
            raise BadArchiveError('L\'encodage de {} n\'est pas de l\'UTF-8.'.format(path))

        return txt

    def _write(self, path, bytes):
        if self.archive is None:
            raise IOError('closed')

        self.archive.writestr(self.archive.getinfo(path), bytes)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
