import logging
from functools import lru_cache
from typing import Any, Callable, Optional, Type, Union

from django.db.models import (
    Field,
    ForeignKey,
    ManyToManyField,
    ManyToOneRel,
    Model,
    OneToOneField,
    QuerySet,
)

logger = logging.getLogger(__name__)

Value = Optional[Union[str, int, float, dict, list, bool]]
FieldTransform = Callable[[Model, str, Any], Value]
InstanceTransform = Callable[[Model, Value], Value]


class UncachedRelationError(Exception):
    pass


def raise_uncached_relation_error(msg):
    raise UncachedRelationError(msg)


def handle_uncached_relation(msg):
    logger.warning(msg)

    # TODO use settings?
    assert raise_uncached_relation_error(msg)


def single_relation(transforms: list[InstanceTransform]) -> FieldTransform:
    def transform(instance: Model, name: str, data: dict):
        if not getattr(instance._meta.model, name).is_cached(instance):
            # TODO check that this works with prefetch_related?
            handle_uncached_relation(
                f"Field {name} is missing select_related or prefetch_related"
            )

        data[name] = instance_to_value(getattr(instance, name), transforms)

    return transform


def many_relations(transforms: list[InstanceTransform]) -> FieldTransform:
    def transform(instance: Model, name: str, data: dict):
        if name not in getattr(instance, "_prefetched_objects_cache", []):
            handle_uncached_relation(f"Field {name} is missing prefetch_related")

        data[name] = [
            instance_to_value(relation_instance, transforms)
            for relation_instance in instance._prefetched_objects_cache[name]
        ]

    return transform


def _select_fields(
    instance: Model, fields: list[Field], data: Value, **kwargs: FieldTransform
) -> Value:
    for field in fields:
        if field.name in kwargs:
            # TODO could have automatic introspection here? make single_relation and many_relations private
            kwargs[field.name](instance, field.name, data)

        elif isinstance(field, ForeignKey) or isinstance(field, OneToOneField):
            single_relation([pk()])(instance, field.name, data)
        elif isinstance(field, ManyToManyField):
            many_relations([pk()])(instance, field.name, data)
        elif isinstance(field, ManyToOneRel):
            many_relations([pk()])(instance, field.get_accessor_name(), data)
        else:
            data[field.name] = getattr(instance, field.name)

    return data


def _field_name(field):
    if isinstance(field, ManyToOneRel):
        return field.get_accessor_name()
    return field.name


@lru_cache(maxsize=1024)
def model_fields(model: Type[Model]):
    return {_field_name(field): field for field in model._meta.get_fields()}


def all_fields(**kwargs: FieldTransform) -> InstanceTransform:
    def transform(instance: Model, data: Value) -> Value:
        _model_fields = model_fields(instance._meta.model)
        return _select_fields(instance, list(_model_fields.values()), data, **kwargs)

    return transform


def model_serializer_fields(
    model_serializer, **kwargs: FieldTransform
) -> InstanceTransform:
    _meta = getattr(model_serializer, "Meta", None)
    if _fields := getattr(_meta, "fields", None):
        return fields(_fields, **kwargs)

    if _exclude := getattr(_meta, "exclude", None):
        return exclude(_exclude, **kwargs)

    raise ValueError("No fields or exclude found in ModelSerializer")


def fields(names: list[str], **kwargs: FieldTransform) -> InstanceTransform:
    for key in kwargs.keys():
        if key not in names:
            names.append(key)

    def transform(instance: Model, data: Value):
        _model_fields = model_fields(instance._meta.model)
        return _select_fields(
            instance,
            [_model_fields[name] for name in names],
            data,
            **kwargs,
        )

    return transform


def exclude(exclude_names: list[str], **kwargs: FieldTransform) -> InstanceTransform:
    for key in kwargs.keys():
        if key not in exclude_names:
            exclude_names.append(key)

    def transform(instance: Model, data: Value):
        _model_fields = model_fields(instance._meta.model)
        return _select_fields(
            instance,
            [
                _model_fields[name]
                for name in _model_fields.keys()
                if name not in exclude_names
            ],
            data,
            **kwargs,
        )

    return transform


def pk() -> InstanceTransform:
    def transform(instance: Model, _):
        # TODO instance.pk is "slow", cache the PK for model
        return instance.pk

    return transform


def instance_to_value(
    instance: Optional[Model], transforms: list[InstanceTransform]
) -> Any:
    if instance is None:
        return None

    data: Value = {}
    for transform in transforms:
        data = transform(instance, data)
    return data


def qs_to_list(qs: QuerySet, transforms: list[InstanceTransform]):
    return [instance_to_value(instance, transforms) for instance in qs]
