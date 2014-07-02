# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import collections
import six


class BaseNodeError(Exception):
    pass

class PatternNodeError(BaseNodeError):
    pass

class ValueNodeError(BaseNodeError):
    pass


class BaseValueNode(object):
    value = None

    def __init__(self, raw, pattern):
        self.raw = raw
        self.pattern = pattern

    def __repr__(self):
        if self.value is not None:
            return repr(self.value)
        return super(BaseValueNode, self).__repr__()


class PrimitiveValueNode(BaseValueNode):
    pass


class DictValueNode(BaseValueNode, dict):

    def __init__(self, *args, **kwargs):
        super(DictValueNode, self).__init__(*args, **kwargs)
        dict.__init__(self)


class ListValueNode(BaseValueNode, list):

    def __init__(self, *args, **kwargs):
        super(ListValueNode, self).__init__(*args, **kwargs)
        list.__init__(self)


class DefaultValueMixin(object):

    def __init__(self, **kwargs):
        self.default = kwargs.pop('default', None)
        super(DefaultValueMixin, self).__init__(**kwargs)

    def parse(self, value):
        if value is None and self.default is not None:
            value = self.default
        return super(DefaultValueMixin, self).parse(value)


class RequiredValueMixin(object):

    def __init__(self, **kwargs):
        self.required = bool(kwargs.pop('required', None))
        super(RequiredValueMixin, self).__init__(**kwargs)

    def parse(self, value):
        if value is None and self.required:
            raise ValueNodeError('{} requires a value'.format(getattr(self, 'name', type(self))))
        return super(RequiredValueMixin, self).parse(value)


class BasePatternNode(object):

    value_class = PrimitiveValueNode

    def __init__(self, **kwargs):
        if kwargs:
            raise PatternNodeError(
                '{} does not accept {}'.format(type(self), ', '.join([attr for attr in kwargs]))
            )

    def parse(self, value):
        if value is None:
            return None
        obj = self.value_class(value, self)
        obj.value = self.clean(value) if value is not None else None
        return obj

    def clean(self, value):
        raise NotImplementedError()


class StringPatternNode(RequiredValueMixin, DefaultValueMixin, BasePatternNode):

    def __init__(self, **kwargs):
        super(StringPatternNode, self).__init__(**kwargs)

    def clean(self, value):
        # force unicode
        if not isinstance(value, six.text_type):
            try:
                value = value.decode('utf-8')
            # not a bytes obj
            except AttributeError:
                value = self.clean(repr(value))
        return value


class NumericPatternNode(RequiredValueMixin, DefaultValueMixin, BasePatternNode):

    def __init__(self, **kwargs):
        super(NumericPatternNode, self).__init__(**kwargs)

    def clean(self, value):
        try:
            return int(value)
        except: 
            try: 
                return float(value)
            except:
                raise ValueNodeError('{} is not a valid number'.format(value))


class MappingPatternNode(RequiredValueMixin, DefaultValueMixin, BasePatternNode):

    def __init__(self, **kwargs):
        super(MappingPatternNode, self).__init__(**kwargs)

    def __init__(self, table=None, **kwargs):
        table = table if table is not None else kwargs.pop('table', None)
        try:
            self.table = dict(table)
        except (ValueError, TypeError):
            raise PatternNodeError('{} is not a valid mapping type'.format(table))
        super(MappingPatternNode, self).__init__(**kwargs)

    def clean(self, value):
        try:
            return self.table[value]
        except (KeyError, TypeError):
            raise ValueNodeError('failed to map {}'.format(value))

    def reverse(self, value):
        keys = list(self.table.keys())
        values = list(self.table.values())
        result = []
        while True:
            try:
                i = values.index(value)
            except (ValueError):
                break
            else:
                result.append(keys[i])
                keys.pop(i)
                values.pop(i)
        if not result:
            raise ValueNodeError('failed to reverse {}'.format(value))
        if len(result) == 1:
            return result[0]
        return result


class BooleanPatternNode(RequiredValueMixin, DefaultValueMixin, BasePatternNode):

    def __init__(self, **kwargs):
        super(BooleanPatternNode, self).__init__(**kwargs)

    def clean(self, value):
        try:
            return bool(int(value))
        except (ValueError, TypeError): 
            raise ValueNodeError('{} is not a valid boolean value'.format(value))


class ListPatternNode(RequiredValueMixin, DefaultValueMixin, BasePatternNode):

    value_class = ListValueNode

    def __init__(self, item=None, **kwargs):
        # allow a ListPatternNode to be instantiated with item as a positional argument
        item = item if item is not None else kwargs.pop('item', None)
        
        if item is None:
            raise PatternNodeError(
                '{}.__init__ requires an item'.format(type(self))
            )

        super(ListPatternNode, self).__init__(**kwargs)
        # pop the item class
        pattern_type = item.pop('type', None)
        # attempt to instantiate it
        try:
            self.item = pattern_type(**item)
        except TypeError as e:
            raise PatternNodeError(str(e))
        if not isinstance(self.item, BasePatternNode):
            raise PatternNodeError(
                '{} is not {} or a subclass of'.format(pattern_type, 'BasePatternNode')
            )

    def parse(self, value):
        value_obj = super(ListPatternNode, self).parse(value)

        if value_obj is not None:
            items = value_obj.raw
            # assume value is a dictionary with ignorable keys
            try:
                items = list(items.values())
            except AttributeError:
                pass
            # items must be an explicit list/tuple instance
            if not isinstance(items, (list, tuple)):
                raise ValueNodeError('{} is not a valid list instance'.format(items))
            for raw_item_value in items:
                value_obj.append(self.item.parse(raw_item_value))
        return value_obj

    def clean(self, value):
        return None


class DictPatternNode(RequiredValueMixin, DefaultValueMixin, BasePatternNode):

    value_class = DictValueNode

    def __init__(self, items=None, **kwargs):
        self.items = {}

        # allow a DictPatternNode to be instantiated with items as a positional argument
        items = items if items is not None else kwargs.pop('items', None)
        super(DictPatternNode, self).__init__(**kwargs)

        try:
            items = dict(items)
        except (ValueError, TypeError) as e:
            raise PatternNodeError(str(e))

        for key, value in six.iteritems(items):
            try:
                item_options = dict(value)
            except (ValueError, TypeError) as e:
                raise PatternNodeError(str(e))

            item_type = item_options.pop('type', None)
            item_name = item_options.pop('name', None)

            # avoid None and unhashable names
            if item_name is None or not isinstance(item_name, collections.Hashable):
                raise PatternNodeError('{} is not valid dict item key'.format(item_name))

            try:
                item_obj = item_type(**item_options)
            except TypeError as e:
                raise PatternNodeError(str(e))

            if not isinstance(item_obj, BasePatternNode):
                raise PatternNodeError(
                    '{} is not {} or a subclass of'.format(item_type, 'BasePatternNode')
                )

            setattr(item_obj, 'name', item_name)
            self.items[key] = item_obj


    def parse(self, value):
        value_obj = super(DictPatternNode, self).parse(value)

        if value_obj is not None:
            try:
                value_items = dict(value_obj.raw)
            except (ValueError, TypeError) as e:
                raise ValueNodeError(
                    'failed to parse {} ({})'.format(value_obj.raw, str(e))
                )

            for item_key, item in six.iteritems(self.items):
                value_obj[item.name] = item.parse(value_items.pop(item_key, None))

            # Unparsed items left
            if value_items:
                raise ValueNodeError(
                    'the dict keys {} are not expected'.format(', '.join(list(value_items)))
                )
        return value_obj

    def clean(self, value):
        return None

    def item(self, name):
        try:
            components = name.split('__')
        except AttributeError:
            raise PatternNodeError('{} is not a valid item name'.format(name))
        node = self
        while components:
            component = components[0]
            try:
                values = six.itervalues(node.items)
            # not a dict item
            except AttributeError:
                break
            for item in values:
                if item.name == component:
                    node = item
                    break
            else:
                break
            # shift the list
            components.pop(0)
        if components:
            raise PatternNodeError('failed to retrieve {}'.format(name))
        return node


class RootPatternNode(DictPatternNode):
    pass