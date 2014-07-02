# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import six
from julia import node


class BaseValueNodeTestCase(unittest.TestCase):

    class NodeWithBaseValue(node.BasePatternNode):

        value_class = node.BaseValueNode

        def clean(self, value):
            return value

    def test_value_node_keeps_reference_to_pattern_node(self):
        pattern_node = self.NodeWithBaseValue()
        value_node = pattern_node.parse('foo')
        self.assertIs(value_node.pattern, pattern_node)

    def test_value_node_keeps_track_of_raw_value(self):
        pattern_node = self.NodeWithBaseValue()
        value_node = pattern_node.parse('foo')
        self.assertEqual(value_node.raw, 'foo')

    def test_value_node_has_empty_parsed_value(self):
        value_node = node.BaseValueNode('foo', None)
        self.assertIs(value_node.value, None)


class DictValueNodeTestCase(unittest.TestCase):

    class NodeWithDictValue(node.BasePatternNode):

        value_class = node.DictValueNode

        def clean(self, value):
            return value

    def test_dict_value_node_is_a_dict_instance(self):
        value_node = node.DictValueNode(None, None)
        self.assertTrue(isinstance(value_node, dict))

    def test_dict_value_node_behaves_like_dict(self):
        value_node = node.DictValueNode(None, None)

        value_node['foo'] = 'bar'
        self.assertEqual(value_node['foo'], 'bar')

        del value_node['foo']
        with self.assertRaises(KeyError):
            value_node['foo']

    def test_dict_value_node_behaves_like_value_node(self):
        pattern_node = self.NodeWithDictValue()
        value_node = pattern_node.parse({'foo': 'bar', 'ham': 'baz'})
        self.assertIs(value_node.pattern, pattern_node)
        self.assertEqual(value_node.raw, {'foo': 'bar', 'ham': 'baz'})


class ListValueNodeTestCase(unittest.TestCase):

    class NodeWithListValue(node.BasePatternNode):

        value_class = node.ListValueNode

        def clean(self, value):
            return value

    def test_list_value_node_is_a_list_instance(self):
        value_node = node.ListValueNode(None, None)
        self.assertTrue(isinstance(value_node, list))

    def test_list_value_node_behaves_like_a_list(self):
        value_node = node.ListValueNode(None, None)

        value_node.append('foo')
        value_node.append('bar')

        self.assertEqual(value_node[0], 'foo')
        self.assertEqual(value_node[1], 'bar')

        del value_node[0]
        self.assertEqual(value_node[0], 'bar')

        with self.assertRaises(IndexError):
            value_node[1]

    def test_list_value_node_behaves_like_a_value_node(self):
        pattern_node = self.NodeWithListValue()
        value_node = pattern_node.parse(['foo', 'bar', 'ham'])
        self.assertIs(value_node.pattern, pattern_node)
        self.assertEqual(value_node.raw, ['foo', 'bar', 'ham'])


class BasePatternNodeTestCase(unittest.TestCase):

    def test_base_pattern_node_doesnt_accept_args(self):
        self.assertRaises(TypeError, node.BasePatternNode, 'foo', 'bar')

    def test_base_pattern_node_doesnt_accept_more_kwargs(self):
        self.assertRaises(node.PatternNodeError, node.BasePatternNode, foo='foo', bar='bar')

    def test_clean_raises_non_implemented_error(self):
        pattern_node = node.BasePatternNode()
        self.assertRaises(NotImplementedError, pattern_node.parse, 'bar')


class RequiredValueMixinTestCase(unittest.TestCase):

    class ClassWithrRequiredValue(node.RequiredValueMixin, node.BasePatternNode):

        def clean(self, value):
            return value

    def test_node_with_no_value(self):
        pattern_node = self.ClassWithrRequiredValue()
        value_node = pattern_node.parse(None)
        self.assertIs(value_node, None)

    def test_unrequired_node_with_no_value(self):
        pattern_node = self.ClassWithrRequiredValue(required=False)
        value_node = pattern_node.parse(None)
        self.assertIs(value_node, None)

    def test_required_node_with_no_value(self):
        pattern_node = self.ClassWithrRequiredValue(required=True)
        self.assertRaises(node.ValueNodeError, pattern_node.parse, None)

    def test_required_node_with_value(self):
        pattern_node = self.ClassWithrRequiredValue(required=True)
        value_node = pattern_node.parse('foo')
        self.assertEqual(value_node.raw, 'foo')

    def test_node_accepts_truthy_values(self):
        some_truthy_values = (True, 1, '1', '0')

        for truthy_value in some_truthy_values:
            pattern_node = self.ClassWithrRequiredValue(required=truthy_value)
            self.assertRaises(node.ValueNodeError, pattern_node.parse, None)

    def test_node_accepts_falsy_values(self):
        some_falsy_values = (False, 0, None, '')

        for falsy_value in some_falsy_values:
            pattern_node = self.ClassWithrRequiredValue(required=falsy_value)
            value_node = pattern_node.parse(None)
            self.assertIs(value_node, None)


class DefaultValueMixinTestCase(unittest.TestCase):

    class ClassWithDefaultValue(node.DefaultValueMixin, node.BasePatternNode):

        def clean(self, value):
            return value

    def test_default_node_with_no_value(self):
        pattern_node = self.ClassWithDefaultValue()
        value_node = pattern_node.parse(None)
        self.assertEqual(value_node.raw, None)

    def test_default_node_with_no_value(self):
        pattern_node = self.ClassWithDefaultValue(default='foo')
        value_node = pattern_node.parse(None)
        self.assertEqual(value_node.raw, 'foo')

    def test_default_node_with_value(self):
        pattern_node = self.ClassWithDefaultValue(default='foo')
        value_node = pattern_node.parse('bar')
        self.assertEqual(value_node.raw, 'bar')

    def test_non_default_node_with_value(self):
        pattern_node = self.ClassWithDefaultValue(default=None)
        value_node = pattern_node.parse('bar')
        self.assertEqual(value_node.raw, 'bar')


class RequiredDefaultMixinTestCase(unittest.TestCase):

    class ClassWithRequiredDefaultValue(node.RequiredValueMixin, node.DefaultValueMixin, node.BasePatternNode):

        def clean(self, value):
            return value

    def test_required_default_node_with_no_value_fails(self):
        pattern_node = self.ClassWithRequiredDefaultValue(required=True, default='foo')
        self.assertRaises(node.ValueNodeError, pattern_node.parse, None)

    def test_unrequired_default_node_with_no_value_returns_default(self):
        pattern_node = self.ClassWithRequiredDefaultValue(required=False, default='foo')
        value_node = pattern_node.parse(None)
        self.assertEqual(value_node.raw, 'foo')

    def test_unrequired_default_node_with_value_returns_value(self):
        pattern_node = self.ClassWithRequiredDefaultValue(required=False, default='foo')
        value_node = pattern_node.parse('bar')
        self.assertEqual(value_node.raw, 'bar')

    def test_required_default_node_with_value_returns_value(self):
        pattern_node = self.ClassWithRequiredDefaultValue(required=True, default='foo')
        value_node = pattern_node.parse('bar')
        self.assertEqual(value_node.raw, 'bar')


class StringNodeTestCase(unittest.TestCase):

    expected_values = (
        ('0', '0'),
        ('foo', 'foo'),
        (b'bar', 'bar'),
        (0, '0'),
        (110, '110'),
        (True, 'True'),
        ('', ''),
        (b'', ''),
        ('42', '42'),
        (b'42', '42'),
        (42, '42'),
        ([42], '[42]'),
    )

    def test_string_node_parsed_value_is_a_unicode_string(self):
        for raw, expected in self.expected_values:
            string_pattern_node = node.StringPatternNode()
            string_value_node = string_pattern_node.parse(raw)
            self.assertEqual(string_value_node.value, expected)


    def test_string_node_parse_none_returns_none(self):
        string_pattern_node = node.StringPatternNode()
        self.assertIs(string_pattern_node.parse(None), None)

    def test_string_node_parse_none_returns_none_unless_required(self):
        string_pattern_node = node.StringPatternNode(required=True)
        self.assertRaises(node.ValueNodeError, string_pattern_node.parse, None)

    def test_string_node_parse_none_returns_none_unless_default(self):
        string_pattern_node = node.StringPatternNode(default='foo')
        self.assertEqual(string_pattern_node.parse(None).value, 'foo')


class NumericNodeTestCase(unittest.TestCase):

    expected_values = (
        ('-100', -100),
        ('10.12', 10.12),
        ('-1.12', -1.12),
        ('0', 0),
        ('1', 1),
        (b'0', 0),
        ('0', 0),
        (b'1', 1),
        (0, 0),
        (1, 1),
        ('-42', -42),
        (True, 1),
        (False, 0),
    )

    invalid_values = (
        'foo',
        b'bar',
        [],
        {},
        '',
        lambda x: x,
    )

    def test_numeric_node_parsed_value_is_a_number(self):
        for raw, expected in self.expected_values:
            numeric_pattern_node = node.NumericPatternNode()
            numeric_value_node = numeric_pattern_node.parse(raw)
            self.assertEqual(numeric_value_node.value, expected)

    def test_numeric_node_parse_fails_on_invalid_input(self):
        for invalid in self.invalid_values:
            numeric_pattern_node = node.NumericPatternNode()
            self.assertRaises(node.ValueNodeError, numeric_pattern_node.parse, invalid)

    def test_numeric_node_parse_none_returns_none(self):
        numeric_pattern_node = node.NumericPatternNode()
        self.assertIs(numeric_pattern_node.parse(None), None)

    def test_numeric_node_parse_none_returns_none_unless_required(self):
        numeric_pattern_node = node.NumericPatternNode(required=True)
        self.assertRaises(node.ValueNodeError, numeric_pattern_node.parse, None)

    def test_numeric_node_parse_none_returns_none_unless_default(self):
        numeric_pattern_node = node.NumericPatternNode(default='10')
        self.assertEqual(numeric_pattern_node.parse(None).value, 10)


class MappingPatternNodeTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.assertItemsEqual
        except AttributeError:
            cls.assertItemsEqual = cls.assertCountEqual

    def setUp(self):
        self.valid_tables = (
            (('foo', 'bar'), ('spam', 'eggs')),
            list(),  # empty mapping
            tuple(), # same
        )

        self.invalid_tables = (
            'foo',
            42,
            ('foo', 'bar'),
        )

        self.test_table = {'foo': 'bar', 'spam': 'eggs', 'baz': 'ham', 'question': 42, 'truth': True}
        self.valid_tables += (self.test_table,)

    def test_mapping_node_accepts_table_as_keyword_argument(self):
        for valid in self.valid_tables:
            mapping_pattern_node = node.MappingPatternNode(table=valid)

    def test_mapping_node_accepts_table_as_positional_argument(self):
        for valid in self.valid_tables:
            mapping_pattern_node = node.MappingPatternNode(valid)

    def test_mapping_node_fails_on_invalid_mapping_table(self):
        for invalid in self.invalid_tables:
            with self.assertRaises(node.PatternNodeError):
                mapping_pattern_node = node.MappingPatternNode(table=invalid)

    def test_mapping_node_fails_on_invalid_mapping_table_with_table_as_positional_arg(self):
        for invalid in self.invalid_tables:
            with self.assertRaises(node.PatternNodeError):
                mapping_pattern_node = node.MappingPatternNode(invalid)

    def test_mapping_node_maps_key_to_value_on_valid_key(self):
        for test_key, test_value in six.iteritems(self.test_table):
            mapping_pattern_node = node.MappingPatternNode(table=self.test_table)
            self.assertEqual(mapping_pattern_node.parse(test_key).value, test_value)

    def test_mapping_node_maps_fails_to_map_nonexistent_key(self):
        mapping_pattern_node = node.MappingPatternNode(table=self.test_table)
        self.assertRaises(node.ValueNodeError, mapping_pattern_node.parse, 'nonexistent')

    def test_mapping_node_default_key_value(self):
        for test_key, test_value in six.iteritems(self.test_table):
            mapping_pattern_node = node.MappingPatternNode(table=self.test_table, default=test_key)
            self.assertEqual(mapping_pattern_node.parse(None).value, test_value)

    def test_mapping_node_required_passes_non_empty_value(self):
        mapping_pattern_node = node.MappingPatternNode(table=self.test_table, required=True)
        for test_key, test_value in six.iteritems(self.test_table):
            self.assertEqual(mapping_pattern_node.parse(test_key).value, test_value)

    def test_mapping_node_parse_none_returns_none(self):
        mapping_pattern_node = node.MappingPatternNode(table=self.test_table)
        self.assertIs(mapping_pattern_node.parse(None), None)

    def test_mapping_node_parse_none_returns_none_unless_required(self):
        mapping_pattern_node = node.MappingPatternNode(table=self.test_table, required=True)
        self.assertRaises(node.ValueNodeError, mapping_pattern_node.parse, None)

    def test_mapping_node_parse_none_returns_none_unless_default(self):
        mapping_pattern_node = node.MappingPatternNode(table=self.test_table, default='foo')
        self.assertEqual(mapping_pattern_node.parse(None).value, 'bar')

    def test_mapping_node_required_ignores_default_value_on_empty_input(self):
        mapping_pattern_node = node.MappingPatternNode(table=self.test_table, required=True, default='foo')
        self.assertRaises(node.ValueNodeError, mapping_pattern_node.parse, None)

    def test_mapping_reverse_values(self):
        for test_key, test_value in six.iteritems(self.test_table):
            mapping_pattern_node = node.MappingPatternNode(table=self.test_table)
            self.assertEqual(mapping_pattern_node.reverse(test_value), test_key)

    def test_mapping_reverse_same_value_to_multiple_keys(self):
        table = {
            '0': 'foo',
            '1': 'foo',
            '2': 'bar',
            '3': 'ham',
            '42': 'bar',
            '44': 'bar',
            '45': 'spam',
        }
        test_node = node.MappingPatternNode(table=table)

        self.assertItemsEqual(test_node.reverse('foo'), ['0', '1'])
        self.assertItemsEqual(test_node.reverse('bar'), ['2', '42', '44'])
        self.assertItemsEqual(test_node.reverse('ham'), '3')
        self.assertItemsEqual(test_node.reverse('spam'), '45')


class BooleanPattenNodeTestCase(unittest.TestCase):

    expected_values = (
        ('1', True),
        ('10', True),
        (b'0', False),
        ('0', False),
        (b'1', True),
        (0, False),
        (1, True),
        (2, True),
        (3, True),
        (True, True),
        (False, False),
    )

    invalid_values = ('foo', b'bar', [], {}, '', '-10.1',)
    truthy_values = (True, 1, '1', b'1', '10', b'10')
    falsy_values = (False, 0, '0', b'0')

    def test_boolean_node_expected_value(self):
        for raw, expected in self.expected_values:
            boolean_pattern_node = node.BooleanPatternNode()
            self.assertEqual(boolean_pattern_node.parse(raw).value, expected)

    def test_boolean_node_invalid_values(self):
        for invalid_value in self.invalid_values:
            boolean_pattern_node = node.BooleanPatternNode()
            self.assertRaises(node.ValueNodeError, boolean_pattern_node.parse, invalid_value)

    def test_boolean_node_parse_none_returns_none(self):
        boolean_pattern_node = node.BooleanPatternNode()
        self.assertIs(boolean_pattern_node.parse(None), None)

    def test_boolean_node_parse_none_returns_none_unless_default(self):
        for falsy_value in self.falsy_values:
            boolean_pattern_node = node.BooleanPatternNode(default=falsy_value)
            self.assertEqual(boolean_pattern_node.parse(None).value, False)

        for truthy_value in self.truthy_values:
            boolean_pattern_node = node.BooleanPatternNode(default=truthy_value)
            self.assertEqual(boolean_pattern_node.parse(None).value, True)


class ListPatternNodeTestCase(unittest.TestCase):

    def setUp(self):

        self.valid_items = (
            {'type': node.BooleanPatternNode, 'required': False},
            {'type': node.NumericPatternNode, 'required': True},
            {'type': node.BooleanPatternNode, 'required': False},
            {'type': node.ListPatternNode, 'item': {'type': node.ListPatternNode, 'item': {'type': node.StringPatternNode}}},
        )

        self.invalid_items = (
            None,
            {},                 # no type #1
            {'default': 'bar'}, # no type #2
            {'type': str},  # invalid type #1
            {'type': int},  # invalid type #2
            {'type': None}, # invalid type #3
            {'something_different': 'bar'},
            {'type': node.BooleanPatternNode, 'default': 'bar', 'required': False, 'irrelevant_arg': 'ham'}, # extra kwarg
        )

        self.test_item = {'type': node.StringPatternNode, 'default': 'lol'}

    def test_list_pattern_node_fails_without_item_kwarg(self):
        self.assertRaises(node.PatternNodeError, node.ListPatternNode)

    def test_list_pattern_node_is_allowed_to_pass_item_as_positional_argument(self):
        pattern_node = node.ListPatternNode(self.test_item)
        self.assertIsInstance(pattern_node.item, node.StringPatternNode)

    def test_list_pattern_node_passes_valid_item_kwarg(self):
        for valid_item in self.valid_items:
            item_type = valid_item['type']
            list_pattern_node = node.ListPatternNode(item=valid_item)
            self.assertTrue(isinstance(list_pattern_node.item, item_type))

    def test_list_pattern_node_passes_valid_item_positional_arg(self):
        for valid_item in self.valid_items:
            item_type = valid_item['type']
            list_pattern_node = node.ListPatternNode(valid_item)
            self.assertTrue(isinstance(list_pattern_node.item, item_type))

    def test_list_pattern_node_fails_with_invalid_item_kwarg(self):
        for invalid_item in self.invalid_items:
            self.assertRaises(node.PatternNodeError, node.ListPatternNode, item=invalid_item)

    def test_list_pattern_node_fails_with_invalid_item_positional_arg(self):
        for invalid_item in self.invalid_items:
            self.assertRaises(node.PatternNodeError, node.ListPatternNode, invalid_item)

    def test_list_pattern_node_parse_returns_list(self):
        list_pattern_node = node.ListPatternNode(item=self.test_item)
        list_value_node = list_pattern_node.parse(['foo', 'bar', 'ham'])
        self.assertTrue(isinstance(list_value_node, list))
        self.assertTrue(isinstance(list_value_node, node.ListValueNode))

    def test_list_pattern_node_parse_list_returns_parsed_list_elements(self):
        list_pattern_node = node.ListPatternNode(item=self.test_item)
        list_value_node = list_pattern_node.parse(['foo', 'bar', 'ham'])
        self.assertEqual(len(list_value_node), 3)
        for parsed_item in list_value_node:
            self.assertTrue(isinstance(parsed_item.pattern, node.StringPatternNode))
            self.assertTrue(parsed_item.value in ('foo', 'bar', 'ham'))

    def test_list_pattern_node_parse_dict_returns_parsed_dict_values(self):
        list_pattern_node = node.ListPatternNode(item=self.test_item)
        list_value_node = list_pattern_node.parse({'0': 'foo', '20': 'bar', 'spam': 'eggs'})
        self.assertEqual(len(list_value_node), 3)
        for parsed_item in list_value_node:
            self.assertTrue(isinstance(parsed_item.pattern, node.StringPatternNode))
            self.assertTrue(parsed_item.value in ('foo', 'bar', 'eggs'))

    def test_list_value_node_parsed_attr_remains_none(self):
        list_pattern_node = node.ListPatternNode(item=self.test_item)
        list_value_node = list_pattern_node.parse(['foo', 'bar', 'ham'])
        self.assertEqual(list_value_node.value, None)

    def test_list_pattern_node_parse_none_returns_none(self):
        list_pattern_node = node.ListPatternNode(item=self.test_item)
        self.assertIs(list_pattern_node.parse(None), None)

    def test_list_pattern_node_parse_none_returns_none_unless_required(self):
        list_pattern_node = node.ListPatternNode(item=self.test_item, required=True)
        self.assertRaises(node.ValueNodeError, list_pattern_node.parse, None)

    def ttest_list_pattern_node_parse_none_returns_none_unless_default(self):
        list_pattern_node = node.ListPatternNode(item=self.test_item, default=('foo', 'bar'))
        list_value_node = list_pattern_node.parse(None)
        for parsed_item in list_value_node:
            self.assertTrue(parsed_item.value in ('foo', 'bar'))


class DictPatternNodeTestCase(unittest.TestCase):

    valid_item_patterns = (
        {},
        tuple(),    # empty mapping
        [],         # same
        [('0', (('name', 'foo'), ('type', node.StringPatternNode)))],
        {'0': {'type': node.StringPatternNode, 'name': 'foo'}},
        {'0': (('type', node.StringPatternNode), ('name', 'foo'))},
        {'0': {'type': node.StringPatternNode, 'name': 'foo'}, '10': {'type': node.BooleanPatternNode, 'name': 'bar'}},
    )

    invalid_item_patterns = (
        None,
        'foo',
        {'0': None},  # no item
        {'0': {}},  # no type, no name
        {'0': {'name': 'foo'}},  # no type #2
        {'0': {'type': None, 'name': 'foo'}},  # invalid type #1
        {'0': {'type': 'ham', 'name': 'foo'}},  # invalid type #2
        {'0': {'type': str, 'name': 'foo'}},  # invalid type #3 
        {'0': {'type': node.StringPatternNode}},  # no name
        {'0': {'type': node.StringPatternNode, 'Name': None}},  # None name
        {'0': {'type': node.StringPatternNode, 'name': []}},  # unhashable name
    )

    valid_item_values = (
        {'10': 'bar', '20': 42},
        {},
        (),  # empty mapping
        [],  # same
    )


    invalid_item_values = (
        'foo',
        0,
        False,
        (('foo', 'bar'), ('spam', 'eggs', '42')),  # invalid mapping
    )

    def setUp(self):
        self.test_item = {
            '10': {
                'type': node.StringPatternNode, 'name': 'foo', 'default': 'ham',
            },
            '20': {
                'type': node.NumericPatternNode, 'name': 'bar', 'default': '42',
            },
        }

    def test_dict_pattern_node_requires_items_keyword(self):
        self.assertRaises(node.PatternNodeError, node.DictPatternNode)

    def test_dict_pattern_node_accepts_items_as_positional_argument(self):
        pattern_node = node.DictPatternNode(self.test_item)
        self.assertIsInstance(pattern_node.item('foo'), node.StringPatternNode)

    def test_dict_pattern_fails_on_invalid_pattern_items(self):
        for invalid in self.invalid_item_patterns:
            self.assertRaises(node.PatternNodeError, node.DictPatternNode, items=invalid)

    def test_dict_pattern_fails_on_invalid_pattern_items_with_items_as_positional_arg(self):
        for invalid in self.invalid_item_patterns:
            self.assertRaises(node.PatternNodeError, node.DictPatternNode, invalid)

    def test_dict_pattern_passes_on_valid_pattern_items(self):
        for valid in self.valid_item_patterns:
            dict_pattern_node = node.DictPatternNode(items=valid)

    def test_dict_pattern_passes_on_valid_pattern_items_with_items_as_positional_arg(self):
        for valid in self.valid_item_patterns:
            dict_pattern_node = node.DictPatternNode(valid)

    def test_dict_pattern_items_are_subclasses_of_base_pattern_node(self):
        for valid in self.valid_item_patterns:
            dict_pattern_node = node.DictPatternNode(items=valid)
            self.assertTrue(len(dict_pattern_node.items) == len(valid))
            for pattern_item_key, pattern_item_value in six.iteritems(dict_pattern_node.items):
                self.assertTrue(isinstance(pattern_item_value, node.BasePatternNode))

    def test_dict_pattern_parse_expects_valid_mapping(self):
        for valid in self.valid_item_values:
            dict_pattern_node = node.DictPatternNode(items=self.test_item)
            dict_pattern_value = dict_pattern_node.parse(valid)
            self.assertTrue(isinstance(dict_pattern_value, dict))
            self.assertTrue(isinstance(dict_pattern_value, node.BaseValueNode))
            self.assertEqual(len(dict_pattern_value), len(self.test_item))

        for invalid in self.invalid_item_values:
            dict_pattern_node = node.DictPatternNode(items=self.test_item)
            self.assertRaises(node.ValueNodeError, dict_pattern_node.parse, invalid)

    def test_dict_pattern_parse_none_returns_none(self):
        dict_pattern_node = node.DictPatternNode(items=self.test_item)
        self.assertIs(dict_pattern_node.parse(None), None)

    def test_dict_pattern_parse_none_returns_none_unless_required(self):
        dict_pattern_node = node.DictPatternNode(items=self.test_item, required=True)
        self.assertRaises(node.ValueNodeError, dict_pattern_node.parse, None)

    def test_dict_pattern_parse_none_returns_none_unless_default(self):
        dict_pattern_node = node.DictPatternNode(items=self.test_item, default={'10': 'baz', '20': '42'})
        dict_value_node = dict_pattern_node.parse(None)
        self.assertIsNot(dict_value_node, None)
        self.assertEqual(dict_value_node['foo'].value, 'baz')
        self.assertEqual(dict_value_node['bar'].value, 42)

    def test_dict_pattern_parse_fails_on_extra_items(self):
        dict_pattern_node = node.DictPatternNode(items=self.test_item)
        self.assertRaises(node.ValueNodeError, dict_pattern_node.parse, {'10': 'baz', '20': '42', 'extra_key': None})

    def test_dict_pattern_parse_fails_on_missing_items(self):
        self.test_item['20']['required'] = True

        dict_pattern_node = node.DictPatternNode(items=self.test_item)
        self.assertRaises(node.ValueNodeError, dict_pattern_node.parse, {})  # 20 is required
        self.assertRaises(node.ValueNodeError, dict_pattern_node.parse, {'10': 'baz'})  # same


class DictPatternNodeItemTraversalTestCase(unittest.TestCase):

    test_pattern = {
        '0': {
            'type': node.DictPatternNode,
            'name': 'foo',
            'items': {
                '0': {
                    'name': 'bar',
                    'type': node.StringPatternNode,
                },
                '1': {
                    'name': 'baz',
                    'type': node.DictPatternNode,
                    'items': {
                        '0': {
                            'type': node.MappingPatternNode,
                            'name': 'spam',
                            'table': {}
                        },
                    },
                },
            },
        },
        '1': {
            'name': 'spam',
            'type': node.StringPatternNode,
        }
    }

    ok_values = (
        ('foo', node.DictPatternNode),
        ('spam', node.StringPatternNode),
        ('foo__bar', node.StringPatternNode),
        ('foo__baz__spam', node.MappingPatternNode),
    )

    invalid_values = (
        None,
        1,
        True,
        tuple(),
        'foo__ham',
        'spam__bar',
        'bar__ham',
        'bar__spam',
        'foo__baz__ham',
    )

    def setUp(self):
        self.test_pattern_node = node.RootPatternNode(items=self.test_pattern)

    def test_dict_pattern_node_item_traversal(self):
        for name, node_class in self.ok_values:
            self.assertTrue(isinstance(self.test_pattern_node.item(name), node_class))

    def test_dict_pattern_node_item_traversal_rases_exception(self):
        for name in self.invalid_values:
            self.assertRaises(node.PatternNodeError, self.test_pattern_node.item, name)