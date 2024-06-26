# 3.0.2 (django-enumfields2, released 2022-12-29)

* Corrected metadata, no functional changes.

# 3.0.1 (django-enumfields2, released 2022-12-29)

* Support `Enum(...)` style construction on Python 3.11 too.

# 3.0.0 (django-enumfields2, released 2022-12-29)

* Remove support for old versions of Django and Python.
* Add support for Python 3.11.
* Add support for deferred fields.

# 2.1.1 (released 2021-02-23)

* Fix string-to-enum conversion regression mistakenly
  introduced in 2.1.0

# 2.1.0 (released 2021-02-22)

* Drop support for Django 2.0
* Drop support for Django 2.1
* Add support for Django 3.1
* Add support for Python 3.9.2+

# 2.0.0 (released 2020-01-18)

## Version support changes (possibly breaking)

* Drop support for Python 2.7
* Drop support for Python 3.4
* Drop support for Django 1.8
* Drop support for Django 1.10
* Add support for Django 2.1
* Add support for Django 2.2
* Add support for Django 3.0
* Add support for Python 3.7
* Add support for Python 3.8

## Additions and bugfixes

* Bug: Fix EnumSupportSerializerMixin for non-editable fields
* Docs: Readme improvements
* Feature: Warn when some values of an enum won't fit in the backing database field
* Packaging: PEP-396 compliant `__version__` attribute
* Packaging: Tests are now packaged with the source distribution
