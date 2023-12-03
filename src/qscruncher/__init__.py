from typing import Any, Optional

from django.db.models import Model, QuerySet

from .qscruncher import (
    FieldTransform,
    InstanceTransform,
    UncachedRelationError,
    all_fields,
    exclude as _exclude,
    fields as _fields,
    instance_to_value as _instance_to_value,
    model_serializer_fields,
    pk,
    qs_to_list as _qs_to_list,
    ref as _ref,
    refs as _refs,
)


def fields(*names: str, **kwargs: FieldTransform) -> InstanceTransform:
    return _fields(names, **kwargs)


def exclude(*exclude_names: str, **kwargs: FieldTransform) -> InstanceTransform:
    return _exclude(exclude_names, **kwargs)


def ref(*transforms: InstanceTransform) -> FieldTransform:
    return _ref(transforms)


def refs(*transforms: InstanceTransform) -> FieldTransform:
    return _refs(transforms)


def instance_to_value(instance: Optional[Model], *transforms: InstanceTransform) -> Any:
    return _instance_to_value(instance, transforms)


def qs_to_list(qs: QuerySet, *transforms: InstanceTransform):
    return _qs_to_list(qs, transforms)
