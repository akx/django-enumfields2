from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from django.core import checks
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.db.models.query_utils import DeferredAttribute
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from .forms import EnumChoiceField

if TYPE_CHECKING:
    from django.forms import Field as FormField

    _MixinBase = models.Field
else:
    # Do not complicate type hierarchy at runtime
    _MixinBase = object


class CastOnAssignDescriptor(DeferredAttribute):
    def __set__(self, obj: models.Model, value: Any) -> None:
        obj.__dict__[self.field.name] = self.field.to_python(value)


class EnumFieldMixin(_MixinBase):  # type: ignore[type-arg]
    descriptor_class = CastOnAssignDescriptor
    enum: type[Enum]

    def __init__(self, enum: type[Enum] | str, **options: Any) -> None:
        if isinstance(enum, str):
            self.enum = import_string(enum)
        else:
            self.enum = enum

        if "choices" not in options:
            options["choices"] = [  # choices for the TypedChoiceField
                (i, getattr(i, 'label', i.name))
                for i in self.enum
            ]

        super().__init__(**options)

    def contribute_to_class(self, cls: type[models.Model], name: str, private_only: bool = False) -> None:
        super().contribute_to_class(cls, name, private_only=private_only)
        setattr(cls, name, CastOnAssignDescriptor(self))

    def to_python(self, value: Any) -> Enum | None:
        if value is None or value == '':
            return None
        try:
            return self.enum(value)
        except ValueError:
            for m in self.enum:
                if value == m:
                    return m
                if value == m.value or str(value) == str(m.value) or str(value) == str(m):
                    return m
        raise ValidationError('{} is not a valid value for enum {}'.format(value, self.enum), code="invalid_enum_value")

    def get_prep_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, self.enum):  # Already the correct type -- fast path
            return value.value
        return self.enum(value).value

    def from_db_value(self, value: Any, expression: Any, connection: Any, *args: Any) -> Enum | None:
        return self.to_python(value)

    def value_to_string(self, obj: Any) -> Any:
        """
        This method is needed to support proper serialization. While its name is value_to_string()
        the real meaning of the method is to convert the value to some serializable format.
        Since most of the enum values are strings or integers we WILL NOT convert it to string
        to enable integers to be serialized natively.
        """
        value = self.value_from_object(obj)
        return value.value if value else None

    def get_default(self) -> Any:
        if self.has_default():
            if self.default is None:
                return None

            if isinstance(self.default, Enum):
                return self.default

            return self.enum(self.default)

        return super().get_default()

    def deconstruct(self) -> tuple[str, str, Any, dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs['enum'] = self.enum
        kwargs.pop('choices', None)
        if 'default' in kwargs:
            if hasattr(kwargs["default"], "value"):
                kwargs["default"] = kwargs["default"].value

        return name, path, args, kwargs

    def get_choices(self, include_blank: bool = True, blank_choice: Any = BLANK_CHOICE_DASH) -> list[tuple[Any, str]]:  # type: ignore[override]
        # Force enum fields' options to use the `value` of the enumeration
        # member as the `value` of SelectFields and similar.
        return [
            (i.value if isinstance(i, Enum) else i, display)  # type: ignore[misc]
            for (i, display)
            in super(EnumFieldMixin, self).get_choices(include_blank, blank_choice)
        ]

    def formfield(  # type: ignore[override]
        self,
        form_class: type[FormField] | None = None,
        choices_form_class: type[EnumChoiceField] | None = None,
        **kwargs: Any,
    ) -> FormField:
        if not choices_form_class:
            choices_form_class = EnumChoiceField

        return super().formfield(  # type: ignore[return-value]
            form_class=form_class,
            choices_form_class=choices_form_class,
            **kwargs
        )


class EnumField(EnumFieldMixin, models.CharField):  # type: ignore[type-arg]
    def __init__(self, enum: type[Enum] | str, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", 10)
        super().__init__(enum, **kwargs)
        self.validators = []

    def check(self, **kwargs: Any) -> list[checks.CheckMessage]:
        return [
            *super().check(**kwargs),
            *self._check_max_length_fit(**kwargs),
        ]

    def _check_max_length_fit(self, **kwargs: Any) -> list[checks.CheckMessage]:
        if isinstance(self.max_length, int):
            unfit_values = [e for e in self.enum if len(str(e.value)) > self.max_length]
            if unfit_values:
                fit_max_length = max([len(str(e.value)) for e in self.enum])
                message = (
                    "Values {unfit_values} of {enum} won't fit in "
                    "the backing CharField (max_length={max_length})."
                ).format(
                    unfit_values=unfit_values,
                    enum=self.enum,
                    max_length=self.max_length,
                )
                hint = "Setting max_length={fit_max_length} will resolve this.".format(
                    fit_max_length=fit_max_length,
                )
                return [
                    checks.Warning(message, hint=hint, obj=self, id="enumfields.max_length_fit"),
                ]
        return []


class EnumIntegerField(EnumFieldMixin, models.IntegerField):  # type: ignore[type-arg]
    @cached_property
    def validators(self) -> list[Any]:
        # Skip IntegerField validators, since they will fail with
        #   TypeError: unorderable types: TheEnum() < int()
        # when used database reports min_value or max_value from
        # connection.ops.integer_field_range method.
        next = super(models.IntegerField, self)
        return next.validators  # type: ignore[attr-defined, no-any-return]

    def get_prep_value(self, value: Any) -> int | None:
        if value is None:
            return None

        if isinstance(value, Enum):
            return value.value  # type: ignore[no-any-return]

        try:
            return int(value)
        except ValueError:
            return self.to_python(value).value  # type: ignore[union-attr, no-any-return]
