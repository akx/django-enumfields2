import inspect
import sys
from enum import Enum as BaseEnum
from enum import EnumMeta as BaseEnumMeta
from enum import _EnumDict

from django.utils.encoding import force_str


class EnumMeta(BaseEnumMeta):
    def __new__(mcs, name, bases, attrs, **kwds):
        if kwds.get('boundary'):
            raise ValueError('boundary should not be set')
        Labels = attrs.get('Labels')

        if Labels is not None and inspect.isclass(Labels):
            del attrs['Labels']
            if hasattr(attrs, '_member_names'):
                if isinstance(attrs._member_names, dict):  # Python 3.11+
                    attrs._member_names.pop('Labels', None)
                else:
                    attrs._member_names.remove('Labels')

        if sys.version_info >= (3, 9, 2):
            attrs._cls_name = name

        obj = BaseEnumMeta.__new__(mcs, name, bases, attrs)
        for m in obj:
            try:
                m.label = getattr(Labels, m.name)
            except AttributeError:
                m.label = m.name.replace('_', ' ').title()

        return obj


class Enum(EnumMeta('Enum', (BaseEnum,), _EnumDict())):
    @classmethod
    def choices(cls):
        """
        Returns a list formatted for use as field choices.
        (See https://docs.djangoproject.com/en/dev/ref/models/fields/#choices)
        """
        return tuple((m.value, m.label) for m in cls)

    def __str__(self):
        """
        Show our label when Django uses the Enum for displaying in a view
        """
        return force_str(self.label)


class IntEnum(int, Enum):
    def __str__(self):  # See Enum.__str__
        return force_str(self.label)
