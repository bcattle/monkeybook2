import re
from monkeybook import app
from monkeybook.getter import ResultGetter, process_photo_results
from monkeybook.models import FqlResult
from monkeybook.utils import merge_spaces


class FQLTaskMongoStorage(object):
    """
    A connector to the `FqlResults` collection in the db
    """
    def __init__(self, user):
        self.user = user

    def store(self, query_type, query, results):
        """
        Stores the results of a FQL query to the database
        """
        fql_result = FqlResult(
            user = self.user,
            query_type = query_type,
            query = query,
            results = results
        )
        fql_result.save()

    def retrieve(self, query):
        return FqlResult.objects.first(user=self.user, query=query).results


class Task(object):
    def __init__(self, name=None):
        assert self.on_results
        if name:
            self.name = name
        else:
            self.name = self._get_canonical_name(self.__class__.__name__)

    def _get_canonical_name(self, string):
        return re.sub(r'([A-Z])([A-Z])', r'\1_\2',
                      re.sub(r'([a-zA-Z])([A-Z])', r'\1_\2', string)).lower()[:-5]


class FQLTask(Task):
    """
    Encapsulates a single FQL query
    The optional `storage` and `cache` classes allow the contents
    of a FQL call to be stored and retrieved in lieu of re-running the query
    """
    def __init__(self, name=None):
        assert self.fql
        self.fql = merge_spaces(self.fql)
        self.prefer_cache = app.config.get('FQL_TASK_PREFER_CACHE', False)
        self.store_results = app.config.get('FQL_TASK_STORE_RESULTS', True)
        super(FQLTask, self).__init__(name)

    # Default, just returns a getter
    def on_results(self, results):
        return ResultGetter(results)

    def _make_results(self, results):
        # Return a dict
        return { self.name: self.on_results(results) }

    def run(self, user, **kwargs):
        self.user = user
        self.storage = FQLTaskMongoStorage(user=user)
        self.open_graph = user.get_fb_api()

        if self.prefer_cache:
            # Check the cache for the query
            cache_result = self.storage.retrieve(self.fql)
            if cache_result:
                return self._make_results(cache_result)

        self.fql_results = self.open_graph.fql(self.fql)

        # TODO: if there was an error, look in the cache as a fallback
        if self.store_results:
            # Store the results, using the storage class
            self.storage.store(
                query_type=self.name,
                query=self.fql,
                results=self.fql_results,
            )
        return self._make_results(self.fql_results)

    def save(self, results):
        raise NotImplementedError()


class BasePhotoResultsTask(FQLTask):
    """
    A task that pulls our standard PHOTO_FIELDS
    """
    def on_results(self, results, photos_i_like):
        getter = process_photo_results(results)
        return getter

