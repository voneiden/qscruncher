import pytest
from django_test_app.models import (
    RelatedManyToManyModel,
    RelatedModel,
    ReverseModel,
    TestModel,
)
from factory import Faker
from factory.django import DjangoModelFactory
from rest_framework.serializers import ModelSerializer

from qscruncher import (
    all_fields,
    fields,
    instance_to_value,
    qs_to_list,
    single_relation,
)
from qscruncher.qscruncher import (
    UncachedRelationError,
    exclude,
    many_relations,
    model_serializer_fields,
    pk,
)


class TestModelFactory(DjangoModelFactory):
    char_field = Faker("bs")
    text_field = Faker("bs")
    integer_field = Faker("random_number", digits=3)
    float_field = Faker("pyfloat")
    decimal_field = Faker("pydecimal", left_digits=8, right_digits=2)

    class Meta:
        model = TestModel


class RelatedModelFactory(DjangoModelFactory):
    text_field = Faker("bs")

    class Meta:
        model = RelatedModel


class RelatedManyToManyFactory(DjangoModelFactory):
    text_field = Faker("bs")

    class Meta:
        model = RelatedManyToManyModel


@pytest.mark.django_db
def test_fields():
    instance = TestModelFactory()
    result = {}
    fields(["id"])(instance, result)
    assert result == {"id": instance.id}


@pytest.fixture
def cached_instance():
    TestModelFactory()
    instance = (
        TestModel.objects.all()
        .select_related(
            "foreign_key",
            "one_to_one_field",
        )
        .prefetch_related("reversemodel_set", "many_to_many_field")[0]
    )
    return instance


@pytest.fixture
def cached_instance_with_foreign_key():
    related = RelatedModelFactory()
    TestModelFactory(foreign_key=related)
    instance = (
        TestModel.objects.all()
        .select_related(
            "foreign_key",
            "one_to_one_field",
        )
        .prefetch_related("reversemodel_set", "many_to_many_field")[0]
    )
    return instance


@pytest.mark.django_db
def test_exclude(cached_instance):
    result = {}
    exclude(["id"])(cached_instance, result)
    assert len(result) > 0
    assert "id" not in result


@pytest.mark.django_db
def test_all_fields(cached_instance):
    result = {}
    all_fields()(cached_instance, result)
    assert len(result) > 0
    assert "id" in result


@pytest.mark.django_db
def test_model_serializer_fields(cached_instance):
    class TestModelSerializer:
        class Meta:
            fields = ("id", "foreign_key")

    assert model_serializer_fields(TestModelSerializer)(cached_instance, {}) == fields(
        ["id", "foreign_key"]
    )(cached_instance, {})


@pytest.mark.django_db
def test_model_serializer_exclude(cached_instance):
    class TestModelSerializer:
        class Meta:
            exclude = ("id", "foreign_key")

    assert model_serializer_fields(TestModelSerializer)(cached_instance, {}) == exclude(
        ["id", "foreign_key"]
    )(cached_instance, {})


@pytest.mark.django_db
def test_model_serializer_meta_missing():
    class TestModelSerializer:
        pass

    with pytest.raises(ValueError):
        model_serializer_fields(TestModelSerializer)


@pytest.mark.django_db
def test_select_kwargs(cached_instance_with_foreign_key):
    result = {}
    all_fields(foreign_key=single_relation([fields(["id"])]))(
        cached_instance_with_foreign_key, result
    )
    assert result["foreign_key"] == {
        "id": cached_instance_with_foreign_key.foreign_key.id
    }
    assert "id" in result


@pytest.mark.django_db
def test_single_relation_no_cache():
    instance = TestModelFactory()
    result = {}
    with pytest.raises(UncachedRelationError):
        single_relation([fields(["foreign_key"])])(instance, "foreign_key", result)


@pytest.mark.django_db
def test_single_relation_select_related():
    TestModelFactory()
    instance = TestModel.objects.all().select_related("foreign_key")[0]
    result = {}
    single_relation([fields(["foreign_key"])])(instance, "foreign_key", result)
    assert "foreign_key" in result
    assert result["foreign_key"] is None


@pytest.mark.django_db
def test_single_relation_prefetch_related():
    TestModelFactory()
    instance = TestModel.objects.all().prefetch_related("foreign_key")[0]
    result = {}
    single_relation([fields(["foreign_key"])])(instance, "foreign_key", result)
    assert "foreign_key" in result
    assert result["foreign_key"] is None


@pytest.mark.django_db
def test_many_relations_no_cache():
    instance = TestModelFactory()
    result = {}
    with pytest.raises(UncachedRelationError):
        many_relations([fields(["many_to_many_field"])])(
            instance, "many_to_many_field", result
        )


@pytest.mark.django_db
def test_many_relations_prefetch_related():
    TestModelFactory()
    instance = TestModel.objects.all().prefetch_related("many_to_many_field")[0]
    result = {}
    many_relations([fields(["many_to_many_field"])])(
        instance, "many_to_many_field", result
    )
    assert "many_to_many_field" in result
    assert result["many_to_many_field"] == []


@pytest.mark.django_db
def test_pk():
    instance = TestModelFactory()
    assert pk()(instance, None) == instance.pk


# todo test automatic adding of field


@pytest.mark.django_db
def test_django():
    test_model = TestModelFactory()
    reverse = ReverseModel.objects.create(relation=test_model)

    assert qs_to_list(
        TestModel.objects.all()
        .select_related("foreign_key", "one_to_one_field")
        .prefetch_related("many_to_many_field", "reversemodel_set"),
        [all_fields()],
    ) == [
        {
            "char_field": test_model.char_field,
            "date_field": test_model.date_field,
            "date_time_field": test_model.date_time_field,
            "decimal_field": test_model.decimal_field,
            "float_field": test_model.float_field,
            "foreign_key": test_model.foreign_key,
            "id": test_model.id,
            "integer_field": test_model.integer_field,
            "many_to_many_field": [],
            "one_to_one_field": test_model.one_to_one_field,
            "reversemodel_set": [reverse.id],
            "text_field": test_model.text_field,
        }
    ]


@pytest.mark.django_db
@pytest.mark.skip(reason="only for perf testing")
def test_perf():
    test_model = TestModelFactory()
    m2m_models = [RelatedManyToManyFactory() for _ in range(1000)]
    test_model.many_to_many_field.set(m2m_models)

    class ManyToManyModelSerializer(ModelSerializer):
        class Meta:
            model = RelatedManyToManyModel
            fields = "__all__"

    class TestModelSerializer(ModelSerializer):
        many_to_many_field = ManyToManyModelSerializer(many=True)
        reversemodel_set = ManyToManyModelSerializer(many=True)

        class Meta:
            model = TestModel
            fields = "__all__"

    qs = list(
        TestModel.objects.all()
        .select_related("foreign_key", "one_to_one_field")
        .prefetch_related("many_to_many_field", "reversemodel_set")
    )

    import timeit

    print(
        "qs_to_list:",
        timeit.timeit(lambda: qs_to_list(qs, [all_fields()]), number=1000),
    )

    print(
        "Model serializer:",
        timeit.timeit(lambda: TestModelSerializer(qs, many=True).data, number=1000),
    )

    import cProfile

    with cProfile.Profile() as pf:
        for i in range(1000):
            qs_to_list(qs, [all_fields()])
    pf.print_stats("tottime")


@pytest.mark.django_db
@pytest.mark.skip(reason="dev testing")
def test_serpy():
    import serpy

    m = TestModelFactory()

    class SimpleS(serpy.Serializer):
        text_field = serpy.Field()

    import timeit

    print("serpy", timeit.timeit(lambda: SimpleS(m).data, number=10000))
    tfs = [fields(["text_field"])]
    print("qscuncher", timeit.timeit(lambda: instance_to_value(m, tfs), number=10000))
