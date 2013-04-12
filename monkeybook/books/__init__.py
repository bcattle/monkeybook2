from monkeybook.utils import get_class_from_string


class Book(object):
    def __init__(self, title, cover, url_prefix, module_prefix,
                 run_task_name='tasks.run_book', settings_module='settings',
                 template='yearbook.html'):
        self.title = title
        self.cover = cover
        self.url_prefix = url_prefix,
        self.module_prefix = module_prefix
        self._run_task_name = run_task_name
        self.settings_module = settings_module
        self.template = template

    @property
    def run_task_name(self):
        return '.'.join(('monkeybook.books', self.module_prefix, self._run_task_name,))

    @property
    def run_task(self):
        return get_class_from_string(self.run_task_name)

    @property
    def settings(self):
        raise NotImplementedError


ALL_BOOKS = {
    'yearbook2012': Book(
        title='2012 Yearbook',
        cover='img/book_icon_144.png',
        url_prefix='yearbook',
        module_prefix='yearbook2012',
    )
}


# '2012yearbook': {
#     'title':         '2012 Yearbook',
#     'cover':         'img/book_icon_144.png',
#     'app_prefix':    'yearbook2012',
#     # 'settings':      'settings',
#     'run_task':      'tasks.run_book',
#     # 'page_factory':  'page_factory.Yearbook2012PageFactory',
#     'url_prefix':    'yearbook',
#     'template':      'yearbook.html'
# }
