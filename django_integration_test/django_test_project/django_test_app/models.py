from django.db.models import (
    CASCADE,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    FloatField,
    ForeignKey,
    IntegerField,
    ManyToManyField,
    Model,
    OneToOneField,
    TextField,
)


class TestModel(Model):
    char_field = CharField(max_length=255)
    text_field = TextField()
    date_field = DateField(auto_now_add=True)
    date_time_field = DateTimeField(auto_now_add=True)
    decimal_field = DecimalField(max_digits=10, decimal_places=2)
    integer_field = IntegerField()
    float_field = FloatField()

    foreign_key = ForeignKey(
        "django_test_app.RelatedModel", on_delete=CASCADE, null=True
    )
    one_to_one_field = OneToOneField(
        "django_test_app.RelatedOneToOneModel", on_delete=CASCADE, null=True
    )
    many_to_many_field = ManyToManyField("django_test_app.RelatedManyToManyModel")


class RelatedModel(Model):
    text_field = TextField()


class RelatedOneToOneModel(Model):
    text_field = TextField()


class RelatedManyToManyModel(Model):
    text_field = TextField()


class ReverseModel(Model):
    relation = ForeignKey("TestModel", on_delete=CASCADE)
