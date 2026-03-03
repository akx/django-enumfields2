from __future__ import annotations

from typing import Any

from rest_framework.fields import CharField, ChoiceField, Field, IntegerField

from enumfields.drf.fields import EnumField as EnumSerializerField
from enumfields.fields import EnumFieldMixin


class EnumSupportSerializerMixin:
    enumfield_options: dict[str, Any] = {}
    enumfield_classes_to_replace: tuple[type[Field], ...] = (ChoiceField, CharField, IntegerField)

    def build_standard_field(self, field_name: str, model_field: Any) -> tuple[type[Field], dict[str, Any]]:
        field_class, field_kwargs = (
            super().build_standard_field(field_name, model_field)  # type: ignore[misc]
        )
        if isinstance(model_field, EnumFieldMixin) and field_class in self.enumfield_classes_to_replace:
            field_class = EnumSerializerField
            field_kwargs['enum'] = model_field.enum
            field_kwargs.update(self.enumfield_options)
        return field_class, field_kwargs
