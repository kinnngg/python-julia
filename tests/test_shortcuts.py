# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import six

from julia import shortcuts, node


class JuliaV1QueryStringTestCase(unittest.TestCase):

    ok_values = (
        (
            '0[0][0][0]=1', 
            {'0': {'0': {'0': {'0': '1'}}}}
        ),
        (
            '0=1&1[0][0]=foo&1[0][1]=bar&1[0][2][0]=ham&1[0][2][1]=baz', 
            {'0': '1', '1': {'0': {'0': 'foo', '1': 'bar', '2': {'0': 'ham', '1': 'baz'}}}}
        ),
        # percent encoded
        (
            '0=1&1%5B0%5D%5B0%5D=foo&1%5B0%5D%5B1%5D=bar&1%5B0%5D%5B2%5D%5B0%5D=ham&1%5B0%5D%5B2%5D%5B1%5D=baz', 
            {'0': '1', '1': {'0': {'0': 'foo', '1': 'bar', '2': {'0': 'ham', '1': 'baz'}}}}
        ),
        (
            'foo[bar]=ham&foo[bar]=baz&foo[spam]=eggs',
            {'foo': {'bar': ['ham', 'baz'], 'spam': 'eggs'}}
        ),
        (
            'foo=ham&foo=baz&foo=eggs',
            {'foo': ['ham', 'baz', 'eggs']}
        ),
        # shadowing
        (
            'foo[foo]=ham&foo[foo]=baz&foo=eggs',
            {'foo': {'foo': ['ham', 'baz']}}
        ),
    )

    def test_julia_v1_query_string_parser_ok_values(self):
        for querystring, expected in self.ok_values:
                self.assertEqual(shortcuts.julia_v1(querystring), expected)


class JuliaV2QueryStringTestCase(unittest.TestCase):

    ok_values = (
        (
            '0.0.0.0=1', 
            {'0': {'0': {'0': {'0': '1'}}}}
        ),
        (
            '0=1&1.0.0=foo&1.0.1=bar&1.0.2.0=ham&1.0.2.1=baz', 
            {'0': '1', '1': {'0': {'0': 'foo', '1': 'bar', '2': {'0': 'ham', '1': 'baz'}}}}
        ),
        (
            'foo.bar=ham&foo.bar=baz&foo.spam=eggs',
            {'foo': {'bar': ['ham', 'baz'], 'spam': 'eggs'}}
        ),
        (
            'foo=ham&foo=baz&foo=eggs',
            {'foo': ['ham', 'baz', 'eggs']}
        ),
        # shadowing
        (
            'foo.foo=ham&foo.foo=baz&foo=eggs',
            {'foo': {'foo': ['ham', 'baz']}}
        ),
        # ignoring empty components
        (
            'foo=ham&foo=baz&foo..=eggs',
            {'foo': ['ham', 'baz', 'eggs']}
        ),
    )

    def test_julia_v2_query_string_parser_ok_values(self):
        for querystring, expected in self.ok_values:
                self.assertEqual(shortcuts.julia_v2(querystring), expected)


class RootPatternNodeParserTestCase(unittest.TestCase):

    test_pattern = {
        '0': {
            'type': node.StringPatternNode,
            'name': 'foo',
            'required': True,
        },
        '1': {
            'type': node.BooleanPatternNode,
            'name': 'bar',
        },
        '3': {
            'type': node.NumericPatternNode,
            'name': 'baz',
        },
        '4': {
            'type': node.DictPatternNode,
            'name': 'spam',
            'items': {
                '0': {
                    'type': node.StringPatternNode,
                    'name': 'eggs',
                },
                '1': {
                    'type': node.NumericPatternNode,
                    'name': '42',
                    'required': True,
                },
            },
        },
    }

    valid_values = (
        '0=bar',
        '0=bar&1=1',
        '0=bar&1=1&4.0=foo&4.1=1',
    )

    invalid_values = (
        '0=bar&10=extra',  # unexpected item
        '0=bar&1=foo',  # invalid boolean value
        '0=bar&1=1&4.0=foo',  # required item missing
    )

    def setUp(self):
        self.test_pattern_node = shortcuts.parse_pattern(self.test_pattern)

    def test_root_pattern_node_instance(self):
        self.assertTrue(isinstance(self.test_pattern_node, node.RootPatternNode))

    def test_root_pattern_node_parse_valid_values(self):
        for valid in self.valid_values:
            self.assertTrue(isinstance(self.test_pattern_node.parse(shortcuts.julia_v2(valid)), node.BaseValueNode))

    def test_root_pattern_node_parse_invalid_values(self):
        for invalid in self.invalid_values:
            self.assertRaises(node.ValueNodeError, self.test_pattern_node.parse, shortcuts.julia_v2(invalid))


class MapValueTestCase(unittest.TestCase):

    test_pattern = {
        '0': {
            'type': node.StringPatternNode,
            'name': 'foo',
        },
        '1': {
            'type': node.DictPatternNode,
            'name': 'spam',
            'items': {
                '0': {
                    'type': node.MappingPatternNode,
                    'name': 'eggs',
                    'table': {
                        '0': 'foo',
                        '1': 'bar',
                        '2': 'ham',
                    }
                },
                '1': {
                    'type': node.NumericPatternNode,
                    'name': '42',
                    'required': True,
                },
                '2': {
                    'type': node.DictPatternNode,
                    'name': 'foo',
                    'items': {
                        '0': {
                            'type': node.MappingPatternNode,
                            'name': '42',
                            'table': {
                                '0': '42',
                            }
                        },
                        '1': {
                            'type': node.DictPatternNode,
                            'name': 'bar',
                            'items': {
                                '0': {
                                    'type': node.MappingPatternNode,
                                    'name': 'spam',
                                    'table': {
                                        '0': 'foo',
                                        '1': 'bar',
                                        '2': 'bar',
                                        '3': 'foo',
                                        '4': 'ham',
                                    }
                                },
                                '1': {
                                    'type': node.NumericPatternNode,
                                    'name': '42',
                                    'required': True,
                                },
                            },
                        },
                    },
                },
            },
        },
        '2': {
            'type': node.BooleanPatternNode,
            'name': 'bar',
        },
        '3': {
            'type': node.MappingPatternNode,
            'name': 'baz',
            'table': {
                '0': 'ham',
                '1': 'spam',
                '2': 'eggs',
            }
        },
    }

    ok_values = (
        ('spam__eggs', '0', 'foo'),
        ('spam__eggs', '1', 'bar'),
        ('spam__eggs', '2', 'ham'),
        ('spam__foo__42', '0', '42'),
        ('baz', '0', 'ham'),
        ('baz', '1', 'spam'),
        ('baz', '2', 'eggs'),
        ('spam__eggs', ['0', '1', '2'], ['foo', 'bar', 'ham']),
        ('spam__eggs', ('0', '1'), ('foo', 'bar')),
        ('baz', ['0', '1', '2'], ['ham', 'spam', 'eggs']),
        ('baz', ('0', '1', '2'), ('ham', 'spam', 'eggs')),
        ('baz', ('0',), ('ham',)),
    )

    reverse_ok_values = (
        ('spam__foo__bar__spam', ['foo', 'bar'], ['0', '1', '2', '3']),
        ('spam__foo__bar__spam', ['foo'], ['0', '3']),
        ('spam__foo__bar__spam', 'foo', ['0', '3']),
        ('spam__foo__bar__spam', ['bar'], ['1', '2']),
        ('spam__foo__bar__spam', 'bar', ['1', '2']),
        ('spam__foo__bar__spam', 'ham', '4'),
    )

    invalid_values = (
        ('spam__eggs', '4'),        # table value out of range
        ('spam__eggs', None),       # invalid key
        ('spam__eggs', 1),          # same 
        ('baz', '5'),               # out of range
        (None, '0'),                # invalid name
        ('bar', '5'),               # not a mapping type
        ('spam__foo__42', '5'),     # same
    )

    @classmethod
    def setUpClass(cls):
        try:
            cls.assertItemsEqual
        except AttributeError:
            cls.assertItemsEqual = cls.assertCountEqual

    def setUp(self):
        self.test_pattern_node = shortcuts.parse_pattern(self.test_pattern)

    def test_ok_values(self):
        for name, value, expected in self.ok_values:
            self.assertEqual(shortcuts.map(self.test_pattern_node, name, value), expected)

    def test_map_invalid_values_raise_base_node_error(self):
        for name, value in self.invalid_values:
            self.assertRaises(node.BaseNodeError, shortcuts.map, self.test_pattern_node, name, value)

    def test_map_accepts_unparsed_pattern(self):
        for name, value, expected in self.ok_values:
            self.assertEqual(shortcuts.map(self.test_pattern, name, value), expected)

    def test_unmap_ok_values(self):
        for name, expected, value in self.ok_values:
            self.assertEqual(shortcuts.unmap(self.test_pattern_node, name, value), expected)
        for name, value, expected in self.reverse_ok_values:
            self.assertItemsEqual(shortcuts.unmap(self.test_pattern_node, name, value), expected)

    def test_map_invalid_values_raise_base_node_error(self):
        for name, value in self.invalid_values:
            self.assertRaises(node.BaseNodeError, shortcuts.map, self.test_pattern_node, name, value)

    def test_unmap_accepts_unparsed_pattern(self):
        for name, expected, value in self.ok_values:
            self.assertEqual(shortcuts.unmap(self.test_pattern, name, value), expected)

    def test_map_coercion(self):
        self.assertEqual(shortcuts.map(self.test_pattern, 'spam__foo__42', '0', coerce=str), '42')
        self.assertEqual(shortcuts.map(self.test_pattern, 'spam__foo__42', '0', coerce=int), 42)
        self.assertEqual(shortcuts.map(self.test_pattern, 'spam__eggs', '0', coerce=str), 'foo')
        self.assertEqual(shortcuts.map(self.test_pattern, 'spam__eggs', '0', coerce=bool), True)

    def test_unmap_coercion(self):
        self.assertEqual(shortcuts.unmap(self.test_pattern, 'spam__foo__bar__spam', 'ham', coerce=str), '4')
        self.assertEqual(shortcuts.unmap(self.test_pattern, 'spam__foo__bar__spam', 'ham', coerce=int), 4)
        self.assertItemsEqual(shortcuts.unmap(self.test_pattern, 'spam__foo__bar__spam', ['foo', 'bar'], coerce=int), [0, 1, 2, 3])
        self.assertItemsEqual(shortcuts.unmap(self.test_pattern, 'spam__foo__bar__spam', ['foo', 'bar'], coerce=bool), [True, True, True, True])