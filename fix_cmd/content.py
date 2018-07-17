# inspired by https://github.com/zestedesavoir/zds-site/blob/dev/zds/tutorialv2/models/versioned.py

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
        pass

    def update_text(self, new_text):
        """Update the text in the extract

        :param new_text: the new extract text
        :type new_text: str
        """

        self.text = new_text


class BadArchiveError(Exception):
    pass


class Content:

    title = ''
    slug = ''
    container = None

    def __init__(self, path):
        self._open(path)

    def _open(self, path):
        """Open a zip file and create a content

            :param path: the path
            :type path: str
            :rtype: Content
            """

        zip_archive = zipfile.ZipFile(path, 'a')

        # is the manifest ok ?
        try:
            manifest = str(zip_archive.read('manifest.json'), 'utf-8')
            json_handler.loads(manifest)
        except KeyError:
            raise BadArchiveError('Cette archive ne contient pas de fichier manifest.json.')
        except UnicodeDecodeError:
            raise BadArchiveError('L\'encodage du manifest.json n\'est pas de l\'UTF-8.')
        except ValueError:
            raise BadArchiveError(
                'Une erreur est survenue durant la lecture du manifest, '
                'vérifiez qu\'il s\'agit de JSON correctement formaté.')
