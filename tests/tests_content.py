from tests import ZdsFixCmdTestCase

from fix_cmd import content


class ContentTestCase(ZdsFixCmdTestCase):
    def test_open_zip(self):
        path = self.copy_to_temporary_directory('article.zip')

        text = 'Ceci est un test évidement!'

        with content.Content(path) as article:
            self.assertEqual(article.type, 'ARTICLE')
            self.assertEqual(article.title, 'Naviguer (presque) sans GPS grâce à la navigation inertielle')
            self.assertEqual(len(article.children), 4)
            self.assertTrue(all(type(c) is content.Extract for c in article.children))

            # read/update
            article.children[0].update_text(text)
            self.assertEqual(article.children[0].get_text(), text)
