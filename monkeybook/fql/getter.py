import datetime
from collections import defaultdict
from pytz import utc
from monkeybook import app
from monkeybook.utils import merge_dicts


class BlankFieldException(Exception):
    pass

class DefaultBlankDict(dict):
    """
    This is an alternative to using a regular `defaultdict`
    because we can't pickle it if it's an instance variable of a class
    """
    def __getitem__(self, item):
        try:
            return super(DefaultBlankDict, self).__getitem__(item)
        except KeyError:
            return ''

class ResultGetter(object):
    """
    An error-tolerant helper class that simplifies
    getting data out of the results returned by facebook
    """
    _ids = None
    _fields_by_id = None
    _ordered = None

    def join_on_field(self, other_getter, map_fxn=None, new_field_name=None,
                      join_field='id', join_field_1=None, join_field_2=None, discard_orphans=True):
        """
        Joins this getter to another by indexing on a field
        and applying a mapping function to generate new outputs
        discard_orphans :   do we discard elements in one that
                            don't match the other?
        """
        if join_field != 'id' or join_field_1 or join_field_2:
            join_field_1 = join_field_1 or join_field
            join_field_2 = join_field_2 or join_field
            getter_by_join_field = {element[join_field_1]: element for element in self.fields}
            other_by_join_field = {element[join_field_2]: element for element in other_getter.fields}
        else:
            getter_by_join_field = self._fields_by_id
            other_by_join_field = other_getter._fields_by_id
        keys_in_both = set(getter_by_join_field) & set(other_by_join_field)
        # Run the mapping function
        if map_fxn:
            joined = [{
                          new_field_name: map_fxn(getter_by_join_field[key], other_by_join_field[key]),
                          # join field is same in both, by definition
                          join_field: getter_by_join_field[key][join_field]
                      } for key in keys_in_both]
        # If no mapping function, just take all existing fields
        else:
            joined = [merge_dicts(getter_by_join_field[key], other_by_join_field[key])
                      for key in keys_in_both]

        if not discard_orphans:
            # Append the orphans
            # Note that this may cause problems if the
            # mapping function introduced any new fields
            [joined.append(getter_by_join_field[key])
             for key in set(getter_by_join_field) - keys_in_both]
            [joined.append(other_by_join_field[key])
             for key in set(other_by_join_field) - keys_in_both]

        # Return a new getter
        return self.from_fields(joined)


    def filter(self, function):
        """
        Filters the elements in this Getter by `function`,
        returning a new getter with the new results set
        """
        pass_filter = filter(function, self.fields)
        return self.from_fields(pass_filter)

    @classmethod
    def from_fields(cls, fields):
        """
        Creates a new getter by setting the fields
        directly, i.e. not parsing them from facebook data
        """
        new_getter = cls([])
        new_fields_by_id = {}
        for element in fields:
            new_fields_by_id[element['id']] = element
        new_getter._fields_by_id = new_fields_by_id
        return new_getter

    @property
    def ids(self):
        if not self._ids:
            self._ids = set(self._fields_by_id.keys())
        return self._ids

    @property
    def fields_by_id(self):
        return self._fields_by_id

    @property
    def fields(self):
        return self._fields_by_id.values()

    def order_by(self, name='id', descending=True):
        """
        Returns a sorted list of the values,
        ordered by the column indicated. Cached.
        """
        if name not in self._ordered:
            self._ordered[name] = sorted(self.fields, key=lambda x: x.get(name), reverse=descending)
        return self._ordered[name]

    def bucket_by_year(self, date_field='created'):
        """
        Returns a tuple (latest_year, results)
        results[year] is a getter for just that year
        """
        fields_by_year = {}
        for item in self.fields:
            item_year = item[date_field].year
            if item_year in fields_by_year:
                fields_by_year[item_year].append(item)
            else:
                fields_by_year[item_year] = [item]
        getters_by_year = {}
        for year, bucket in fields_by_year.items():
            getters_by_year[year] = self.from_fields(bucket)
        max_year = max(getters_by_year.keys())
        return max_year, getters_by_year

    def get_in_decending_year_score_order(self, date_field='created'):
        """
        Returns a flat list of elements, sorted by year
        then by score within each year
        """
        return sorted(self.fields, key=lambda x: (x[date_field].year, x['score']), reverse=True)

    def __len__(self):
        return len(self.ids)

    def __iter__(self):
        return self.fields.__iter__()

    def __getitem__(self, item):
        return self.fields.__getitem__(item)

    def __init__(self, results, id_field='object_id', auto_id_field=False, id_is_int=False,
                 fields=None, field_names=None, defaults=None, optional_fields=None, timestamps=None,
                 integer_fields=None, extra_fields=None):
        """
        extra_fields    a dict of field names to add, and a function to call
                        on the existing entry, for instance to calculate a composite value

                        extra_fields={'likes_and_comments': lambda x: x['like_count'] + x['comment_count']}
        """
        self._ids = None
        if app.config['DEBUG']:
            fail_silently = False
            self._fields_by_id = {}
        else:
            fail_silently = True
            self._fields_by_id = DefaultBlankDict()
        self._ordered = {}

        fields = fields or []
        field_names = field_names or {}
        defaults = defaults or {}
        optional_fields = optional_fields or {}
        extra_fields = extra_fields or {}
        timestamps = timestamps or []
        integer_fields = integer_fields or []

        # If we are generating an auto_id, still want `id_field` in results
        if auto_id_field:
            fields.append(id_field)

        for index, curr_result in enumerate(results):
            processed_fields = {}
            # If we encounter a ValueError or KeyError,
            # scrub the whole entry (poor man's transaction)
            try:
                if auto_id_field:
                    curr_id = index
                else:
                    if id_is_int:
                        curr_id = int(curr_result[id_field])      # fail if no id or not an int
                    else:
                        curr_id = str(curr_result[id_field])      # fail if no id
                for field in fields:
                    f = field.split('.')
                    try:
                        field1_val = curr_result[f[0]]        # fail loudly!
                    except KeyError:
                        # Either substitute a default or
                        # skip if field is optional
                        if field in defaults:
                            field1_val = defaults[field]
                        elif field in optional_fields:
                            continue
                        else:
                            raise
                        # Was it a first or second level field?
                    if len(f) == 1:
                        field_name = field
                        field_val = field1_val
                    else:
                        # f[1] is the actual field name
                        field_name = f[1]       # 'comment_info.comment_count' --> 'comment_count'
                        try:
                            field_val = field1_val[f[1]]        # fail loudly!
                        except KeyError:
                            # Either substitute a default or
                            # skip if field is optional
                            if field in defaults:
                                field_val = defaults[field]
                            elif field in optional_fields:
                                continue
                            else:
                                raise

                    # Is the field blank?
                    # Note: a blank field is not necessarily an error, may be something fb won't let us see
                    if hasattr(field_val, 'strip') and field_val.strip() == '':
                        # Does it have a default or is it optional?
                        if field in defaults:
                            field_val = defaults[field_name]
                        elif field in optional_fields:
                            continue
                        else:
                            # Scrub the entire result
                            raise BlankFieldException(field)

                    # Process the field
                    try:
                        if field in timestamps:
                            if field_val is None:
                                if field in defaults:
                                    val = defaults[field_name]
                                elif field in optional_fields:
                                    continue
                                else:
                                    # Scrub the entire result
                                    raise BlankFieldException(field)
                            else:
                                val = datetime.datetime.utcfromtimestamp(float(field_val)).replace(tzinfo=utc)      # fail loudly!
                        elif field in integer_fields:
                            val = int(field_val)
                        else:
                            # Regular old field
                            val = field_val
                    except ValueError:
                        # Either substitute a default or skip if field is optional
                        if field in defaults:
                            val = defaults[field]
                        elif field in optional_fields:
                            continue
                        else:
                            raise

                    if field in field_names:
                        processed_fields[field_names[field]] = val
                    else:
                        processed_fields[field_name] = val

                processed_fields['id'] = curr_id
                for extra_name, fxn in extra_fields.items():
                    processed_fields[extra_name] = fxn(processed_fields)
                    # add to _fields_by_id
                self._fields_by_id[curr_id] = processed_fields

            except BlankFieldException:
                continue
            except (ValueError, KeyError), e:
                if fail_silently:
                    continue
                else:
                    raise


class FreqDistResultGetter(ResultGetter):
    """
    A result getter that returns the data
    in the form of a list of frequencies in descending order
    """
    def __init__(self, results, id_field='object_id', cutoff=0):
        """
        Elements that occur less-frequently than `cutoff` are discarded
        """
        fail_silently = not app.config['DEBUG']
        self._ids = None
        self._ordered = {}

        #        self.results = results
        fields_by_id = {}
        for curr_result in results:
            try:
                # If we encounter any ValueError or KeyError,
                # scrub the whole entry (poor man's transaction)
                curr_id = int(curr_result[id_field])      # fail loudly!
                if curr_id in fields_by_id:
                    fields_by_id[curr_id]['count'] += 1
                else:
                    fields_by_id[curr_id] = {'id': curr_id, 'count': 1}
            except (ValueError, KeyError):
                if fail_silently:
                    continue
                else:
                    raise

        filtered = filter(lambda x: x['count'] > cutoff, fields_by_id.values())
        self._fields_by_id = {item['id']: item for item in filtered}
        self._ids = set(self._fields_by_id.keys())


def process_photo_results(results, scoring_fxn=None,
                          add_to_fields=None, add_to_defaults=None, commit=True):
    """
    Resolves the fields we know about for photos
    If commit=True, saves them to the db
    """
    fields = ['created', 'height', 'width', 'fb_url',
              'comment_info.comment_count', 'like_info.like_count',
              'images']
    integer_fields = ['height', 'width', 'comment_info.comment_count',
                      'like_info.like_count']
    if add_to_fields:
        fields.extend(add_to_fields)
    add_to_defaults = add_to_defaults or {}

    fb_results = len(results)
    extra_fields = {}
    if scoring_fxn:
        extra_fields['score'] = scoring_fxn

    getter = ResultGetter(
        results,
        fields = fields,
        timestamps = ['created'],
        integer_fields = integer_fields,
        extra_fields = extra_fields,
        defaults=add_to_defaults,
        # fail_silently=False
    )

    getter_results = len(getter)
    if fb_results != getter_results:
        app.logger.warning('Facebook returned %d results, our getter only produced %d' % (fb_results, getter_results))
    #    else:
    #        logger.info('Pulled %d photos' % getter_results)
    if commit:
        FacebookPhoto.objects.from_getter(getter)
    return getter
