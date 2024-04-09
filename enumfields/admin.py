import django
from django.contrib.admin.filters import ChoicesFieldListFilter
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _


def listify(v):
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return v
    return [v]


class EnumFieldListFilter(ChoicesFieldListFilter):
    def choices(self, cl):
        list_val = listify(self.lookup_val)
        yield {
            'selected': list_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All'),
        }
        for enum_value in self.field.enum:
            str_value = force_str(enum_value.value)
            yield {
                'selected': (str_value in list_val if list_val else False),
                'query_string': cl.get_query_string({self.lookup_kwarg: str_value}),
                'display': getattr(enum_value, 'label', None) or force_str(enum_value),
            }

    def queryset(self, request, queryset):
        list_val = listify(self.lookup_val)
        last_val = list_val[-1] if list_val else None
        try:
            self.field.enum(last_val)
        except ValueError:
            # since `used_parameters` will always contain strings,
            # for non-string-valued enums we'll need to fall back to attempt a slower
            # linear stringly-typed lookup.
            for enum_value in self.field.enum:
                if force_str(enum_value.value) == last_val:
                    param_value = enum_value if django.VERSION < (5,) else [enum_value]
                    self.used_parameters[self.lookup_kwarg] = param_value
                    break
        return super().queryset(request, queryset)
