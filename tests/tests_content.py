import os

from tests import ZdsFixCmdTestCase

from fix_cmd import content


class ContentTestCase(ZdsFixCmdTestCase):
    def test_open_zip(self):
        path = self.copy_to_temporary_directory('article.zip')
        text = 'Ceci est un test, évidement ! Ça va aller avec tout ces caractères spéciaux: $^!☢ ?'

        # read
        article = content.Content.extract(path)
        self.assertEqual(article.type, 'ARTICLE')
        self.assertEqual(article.title, 'Naviguer (presque) sans GPS grâce à la navigation inertielle')
        self.assertEqual(len(article.children), 4)
        self.assertTrue(all(type(c) is content.Extract for c in article.children))

        self.assertIn('GPS', article.introduction_value)

        # write
        article.conclusion_value = text
        npath = os.path.join(self.temporary_directory, 'new_article.zip')
        article.save(npath)
        article = content.Content.extract(npath)
        self.assertEqual(article.conclusion_value, text)

    def test_open_zip_tuto(self):
        path = self.copy_to_temporary_directory('tuto.zip')
        text = 'Ceci est un test, évidement ! Ça va aller avec tout ces caractères spéciaux: $^!☢ ?'

        # read
        tuto = content.Content.extract(path)
        self.assertEqual(tuto.type, 'TUTORIAL')
        self.assertEqual(tuto.title, 'Un tuto de test')
        self.assertEqual(len(tuto.children), 2)
        self.assertTrue(all(type(c) is content.Container for c in tuto.children))

        # write
        tuto.children[0].conclusion_value = text
        npath = os.path.join(self.temporary_directory, 'new_tuto.zip')
        tuto.save(npath)
        tuto = content.Content.extract(npath)
        self.assertEqual(tuto.children[0].conclusion_value, text)
