from collections import OrderedDict

from django.test import TestCase

from animesuki.core.models import Language
from .models import object_to_dict, object_data_revert, changed_keys, filter_data

class HistoryTest(TestCase):
    fixtures = ['language.json']

    def test_object_to_dict(self):
        # Get Language object (loaded from fixture)
        lang = Language.objects.all()[:1].get()
        expected = OrderedDict()
        # No 'code' as that is the primary key (which should be omitted)
        expected['name'] = lang.name
        expected['country_code'] = lang.country_code
        # Convert object to dict
        data = object_to_dict(lang)
        self.assertIsInstance(data, OrderedDict)
        self.assertEqual(data, expected)

    def test_object_data_revert(self):
        # Get Language object (loaded from fixture)
        lang = Language.objects.all()[:1].get()
        expected = OrderedDict()
        # No 'code' as that is the primary key (which should be omitted)
        expected['name'] = lang.name
        expected['country_code'] = lang.country_code
        # Change something (function should return fresh data from database)
        lang.name = 'Changed'
        # Get object data revert
        data = object_data_revert(lang)
        self.assertEqual(data, expected)
        # If new object is passed, should return None
        lang = Language()
        data = object_data_revert(lang)
        self.assertIsNone(data)

    def test_changed_keys(self):
        d1 = {'a': 1, 'b': 2, 'c': 3}
        d2 = d1.copy()
        # If both dictionaries are the same, return empty list
        k = changed_keys(d1, d2)
        self.assertEqual(k, [])
        # If values don't match, return key that was different
        d2['b'] = 0
        k = changed_keys(d1, d2)
        self.assertEqual(k, ['b'])
        # If a key is missing, ignore it
        del d2['b']
        k = changed_keys(d1, d2)
        self.assertEqual(k, [])

    def test_filter_data(self):
        d = {'a': 1, 'b': 2, 'c': 3}
        expected = OrderedDict()
        expected['c'] = 3
        expected['b'] = 2
        # Filter data and return only element 'c' and 'b' (in that order)
        data = filter_data(d, ['c', 'b'])
        self.assertIsInstance(data, OrderedDict)
        self.assertEqual(data, expected)
