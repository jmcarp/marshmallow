#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random

import pytest

from marshmallow import Schema, fields, utils, MarshalResult, UnmarshalResult
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import unicode, binary_type

from tests.base import *  # noqa


random.seed(1)

# Run tests with both verbose serializer and "meta" option serializer
@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_serializing_basic_object(SchemaClass, user):
    s = SchemaClass()
    data, errors = s.dump(user)
    assert data['name'] == user.name
    assert_almost_equal(s.data['age'], 42.3)
    assert data['registered']

def test_serializer_dump(user):
    s = UserSchema()
    result, errors = s.dump(user)
    assert result['name'] == user.name
    # Change strict mode
    s.strict = True
    bad_user = User(name='Monty', email='invalid')
    with pytest.raises(MarshallingError):
        s.dump(bad_user)

def test_dump_returns_dict_of_errors():
    s = UserSchema()
    bad_user = User(name='Monty', email='invalidemail', homepage='badurl')
    result, errors = s.dump(bad_user)
    assert 'email' in errors
    assert 'homepage' in errors

def test_dump_returns_a_marshalresult(user):
    s = UserSchema()
    result = s.dump(user)
    assert isinstance(result, MarshalResult)
    data = result.data
    assert isinstance(data, dict)
    errors = result.errors
    assert isinstance(errors, dict)

def test_dumps_returns_a_marshalresult(user):
    s = UserSchema()
    result = s.dumps(user)
    assert isinstance(result, MarshalResult)
    assert isinstance(result.data, binary_type)
    assert isinstance(result.errors, dict)

def test_load_returns_an_unmarshalresult():
    s = UserSchema()
    result = s.load({'name': 'Monty'})
    assert isinstance(result, UnmarshalResult)
    assert isinstance(result.data, User)
    assert isinstance(result.errors, dict)

def test_loads_returns_an_unmarshalresult(user):
    s = UserSchema()
    result = s.loads(json.dumps({'name': 'Monty'}))
    assert isinstance(result, UnmarshalResult)
    assert isinstance(result.data, User)
    assert isinstance(result.errors, dict)

def test_serializing_none():
    s = UserSchema(None)
    assert s.data['name'] == ''
    assert s.data['age'] == 0


@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_fields_are_not_copies(SchemaClass):
    s = SchemaClass(User('Monty', age=42))
    s2 = SchemaClass(User('Monty', age=43))
    assert s.fields is not s2.fields


def test_dumps_returns_json(user):
    ser = UserSchema()
    serialized, errors = ser.dump(user)
    json_data, errors = ser.dumps(user)
    expected = binary_type(json.dumps(serialized).encode("utf-8"))
    assert json_data == expected


def test_dumps_returns_bytestring(user):
    s = UserSchema()
    result, errors = s.dumps(user)
    assert isinstance(result, binary_type)


def test_naive_datetime_field(user, serialized_user):
    expected = utils.isoformat(user.created)
    assert serialized_user.data['created'] == expected

def test_datetime_formatted_field(user, serialized_user):
    result = serialized_user.data['created_formatted']
    assert result == user.created.strftime("%Y-%m-%d")

def test_datetime_iso_field(user, serialized_user):
    assert serialized_user.data['created_iso'] == utils.isoformat(user.created)

def test_tz_datetime_field(user, serialized_user):
    # Datetime is corrected back to GMT
    expected = utils.isoformat(user.updated)
    assert serialized_user.data['updated'] == expected

def test_local_datetime_field(user, serialized_user):
    expected = utils.isoformat(user.updated, localtime=True)
    assert serialized_user.data['updated_local'] == expected

def test_class_variable(serialized_user):
    assert serialized_user.data['species'] == 'Homo sapiens'

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_serialize_many(SchemaClass):
    user1 = User(name="Mick", age=123)
    user2 = User(name="Keith", age=456)
    users = [user1, user2]
    serialized = SchemaClass(users, many=True)
    assert len(serialized.data) == 2
    assert serialized.data[0]['name'] == "Mick"
    assert serialized.data[1]['name'] == "Keith"

def test_no_implicit_list_handling(recwarn):
    users = [User(name='Mick'), User(name='Keith')]
    with pytest.raises(TypeError):
        UserSchema(users)
    w = recwarn.pop()
    assert issubclass(w.category, DeprecationWarning)

def test_inheriting_serializer(user):
    serialized = ExtendedUserSchema(user)
    assert serialized.data['name'] == user.name
    assert not serialized.data['is_old']

def test_custom_field(serialized_user, user):
    assert serialized_user.data['uppername'] == user.name.upper()

def test_url_field(serialized_user, user):
    assert serialized_user.data['homepage'] == user.homepage

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_url_field_validation(SchemaClass):
    invalid = User("John", age=42, homepage="/john")
    s = SchemaClass(invalid)
    assert s.is_valid(["homepage"]) is False

def test_relative_url_field():
    u = User("John", age=42, homepage="/john")
    serialized = UserRelativeUrlSchema(u)
    assert serialized.is_valid()

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_stores_invalid_url_error(SchemaClass):
    user = User(name="John Doe", homepage="www.foo.com")
    serialized = SchemaClass(user)
    assert "homepage" in serialized.errors
    expected = '"www.foo.com" is not a valid URL. Did you mean: "http://www.foo.com"?'
    assert serialized.errors['homepage'] == expected

def test_default():
    user = User("John")  # No ID set
    serialized = UserSchema(user)
    assert serialized.data['id'] == "no-id"

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_email_field(SchemaClass):
    u = User("John", email="john@example.com")
    s = SchemaClass(u)
    assert s.data['email'] == "john@example.com"

def test_stored_invalid_email():
    u = User("John", email="johnexample.com")
    s = UserSchema(u)
    assert "email" in s.errors
    assert s.errors['email'] == '"johnexample.com" is not a valid email address.'

def test_integer_field():
    u = User("John", age=42.3)
    serialized = UserIntSchema(u)
    assert type(serialized.data['age']) == int
    assert serialized.data['age'] == 42

def test_integer_default():
    user = User("John", age=None)
    serialized = UserIntSchema(user)
    assert type(serialized.data['age']) == int
    assert serialized.data['age'] == 0

def test_fixed_field():
    u = User("John", age=42.3)
    serialized = UserFixedSchema(u)
    assert serialized.data['age'] == "42.30"

def test_as_string():
    u = User("John", age=42.3)
    serialized = UserFloatStringSchema(u)
    assert type(serialized.data['age']) == str
    assert_almost_equal(float(serialized.data['age']), 42.3)

def test_decimal_field():
    u = User("John", age=42.3)
    s = UserDecimalSchema(u)
    assert type(s.data['age']) == unicode
    assert_almost_equal(float(s.data['age']), 42.3)

def test_price_field(serialized_user):
    assert serialized_user.data['balance'] == "100.00"


def test_fields_param_must_be_list_or_tuple():
    invalid = User("John", email="johnexample.com")
    with pytest.raises(ValueError):
        UserSchema(invalid).is_valid("name")

def test_extra():
    user = User("Joe", email="joe@foo.com")
    data, errors = UserSchema(extra={"fav_color": "blue"}).dump(user)
    assert data['fav_color'] == "blue"

def test_extra_many():
    users = [User('Fred'), User('Brian')]
    data, errs = UserSchema(many=True, extra={'band': 'Queen'}).dump(users)
    assert data[0]['band'] == 'Queen'

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_method_field(SchemaClass, serialized_user):
    assert serialized_user.data['is_old'] is False
    u = User("Joe", age=81)
    assert SchemaClass(u).data['is_old'] is True

def test_function_field(serialized_user, user):
    assert serialized_user.data['lowername'] == user.name.lower()

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_prefix(SchemaClass, user):
    s = SchemaClass(user, prefix="usr_")
    assert s.data['usr_name'] == user.name

def test_fields_must_be_declared_as_instances(user):
    class BadUserSchema(Schema):
        name = fields.String
    with pytest.raises(TypeError):
        BadUserSchema(user)

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_serializing_generator(SchemaClass):
    users = [User("Foo"), User("Bar")]
    user_gen = (u for u in users)
    s = SchemaClass(user_gen, many=True)
    assert len(s.data) == 2
    assert s.data[0] == SchemaClass(users[0]).data


def test_serializing_empty_list_returns_empty_list():
    assert UserSchema([], many=True).data == []
    assert UserMetaSchema([], many=True).data == []


def test_serializing_dict(user):
    user = {"name": "foo", "email": "foo", "age": 42.3}
    s = UserSchema(user)
    assert s.data['name'] == "foo"
    assert s.data['age'] == 42.3
    assert s.is_valid(['email']) is False

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_exclude_in_init(SchemaClass, user):
    s = SchemaClass(user, exclude=('age', 'homepage'))
    assert 'homepage' not in s.data
    assert 'age' not in s.data
    assert 'name' in s.data

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_only_in_init(SchemaClass, user):
    s = SchemaClass(user, only=('name', 'age'))
    assert 'homepage' not in s.data
    assert 'name' in s.data
    assert 'age' in s.data

def test_invalid_only_param(user):
    with pytest.raises(AttributeError):
        UserSchema(user, only=("_invalid", "name"))

def test_strict_init():
    invalid = User("Foo", email="foo.com")
    with pytest.raises(MarshallingError):
        UserSchema(invalid, strict=True)

def test_strict_meta_option():
    class StrictUserSchema(UserSchema):
        class Meta:
            strict = True
    invalid = User("Foo", email="foo.com")
    with pytest.raises(MarshallingError):
        StrictUserSchema(invalid)

def test_can_serialize_uuid(serialized_user, user):
    assert serialized_user.data['uid'] == str(user.uid)

def test_can_serialize_time(user, serialized_user):
    expected = user.time_registered.isoformat()[:12]
    assert serialized_user.data['time_registered'] == expected

def test_invalid_time():
    u = User('Joe', time_registered='foo')
    s = UserSchema(u)
    assert s.is_valid(['time_registered']) is False
    assert s.errors['time_registered'] == "'foo' cannot be formatted as a time."

def test_invalid_date():
    u = User("Joe", birthdate='foo')
    s = UserSchema(u)
    assert s.is_valid(['birthdate']) is False
    assert s.errors['birthdate'] == "'foo' cannot be formatted as a date."

def test_invalid_selection():
    u = User('Jonhy')
    u.sex = 'hybrid'
    s = UserSchema(u)
    assert s.is_valid(['sex']) is False
    assert s.errors['sex'] == "'hybrid' is not a valid choice for this field."

def test_custom_json():
    class UserJSONSchema(Schema):
        name = fields.String()

        class Meta:
            json_module = mockjson

    user = User('Joe')
    s = UserJSONSchema(user)
    result, errors = s.dumps(user)
    assert result == mockjson.dumps('val')


def test_custom_error_message():
    class ErrorSchema(Schema):
        email = fields.Email(error="Invalid email")
        homepage = fields.Url(error="Bad homepage.")
        balance = fields.Fixed(error="Bad balance.")

    u = User("Joe", email="joe.net", homepage="joe@example.com", balance="blah")
    s = ErrorSchema()
    data, errors = s.dump(u)
    assert errors['email'] == "Invalid email"
    assert errors['homepage'] == "Bad homepage."
    assert errors['balance'] == "Bad balance."


def test_error_raised_if_fields_option_is_not_list():
    class BadSchema(Schema):
        name = fields.String()

        class Meta:
            fields = 'name'

    u = User('Joe')
    with pytest.raises(ValueError):
        BadSchema(u)


def test_error_raised_if_additional_option_is_not_list():
    class BadSchema(Schema):
        name = fields.String()

        class Meta:
            additional = 'email'

    u = User('Joe')
    with pytest.raises(ValueError):
        BadSchema(u)


def test_meta_serializer_fields():
    u = User("John", age=42.3, email="john@example.com",
             homepage="http://john.com")
    s = UserMetaSchema(u)
    assert s.data['name'] == u.name
    assert s.data['balance'] == "100.00"
    assert s.data['uppername'] == "JOHN"
    assert s.data['is_old'] is False
    assert s.data['created'] == utils.isoformat(u.created)
    assert s.data['updated_local'] == utils.isoformat(u.updated, localtime=True)
    assert s.data['finger_count'] == 10

class KeepOrder(Schema):
    name = fields.String()
    email = fields.Email()
    age = fields.Integer()
    created = fields.DateTime()
    id = fields.Integer()
    homepage = fields.Url()
    birthdate = fields.DateTime()

def test_declared_field_order_is_maintained(user):
    ser = KeepOrder()
    data, errs = ser.dump(user)
    keys = list(data)
    assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

def test_nested_field_order_with_only_arg_is_maintained(user):
    class HasNestedOnly(Schema):
        user = fields.Nested(KeepOrder, only=('name', 'email', 'age',
                                              'created', 'id', 'homepage'))
    ser = HasNestedOnly()
    data, errs = ser.dump({'user': user})
    user_data = data['user']
    keys = list(user_data)
    assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage']

def test_nested_field_order_with_exlude_arg_is_maintained(user):
    class HasNestedExclude(Schema):
        user = fields.Nested(KeepOrder, exclude=('birthdate', ))

    ser = HasNestedExclude()
    data, errs = ser.dump({'user': user})
    user_data = data['user']
    keys = list(user_data)
    assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage']


def test_meta_fields_order_is_maintained(user):
    class MetaSchema(Schema):
        class Meta:
            fields = ('name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate')

    ser = MetaSchema()
    data, errs = ser.dump(user)
    keys = list(data)
    assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']


def test_meta_fields_mapping(user):
    s = UserMetaSchema(user)
    assert type(s.fields['name']) == fields.String
    assert type(s.fields['created']) == fields.DateTime
    assert type(s.fields['updated']) == fields.DateTime
    assert type(s.fields['updated_local']) == fields.LocalDateTime
    assert type(s.fields['age']) == fields.Float
    assert type(s.fields['balance']) == fields.Price
    assert type(s.fields['registered']) == fields.Boolean
    assert type(s.fields['sex_choices']) == fields.Raw
    assert type(s.fields['hair_colors']) == fields.Raw
    assert type(s.fields['finger_count']) == fields.Integer
    assert type(s.fields['uid']) == fields.UUID
    assert type(s.fields['time_registered']) == fields.Time
    assert type(s.fields['birthdate']) == fields.Date
    assert type(s.fields['since_created']) == fields.TimeDelta


def test_meta_field_not_on_obj_raises_attribute_error(user):
    class BadUserSchema(Schema):
        class Meta:
            fields = ('name', 'notfound')
    with pytest.raises(AttributeError):
        BadUserSchema(user)

def test_exclude_fields(user):
    s = UserExcludeSchema(user)
    assert "created" not in s.data
    assert "updated" not in s.data
    assert "name" in s.data

def test_fields_option_must_be_list_or_tuple(user):
    class BadFields(Schema):
        class Meta:
            fields = "name"
    with pytest.raises(ValueError):
        BadFields(user)

def test_exclude_option_must_be_list_or_tuple(user):
    class BadExclude(Schema):
        class Meta:
            exclude = "name"
    with pytest.raises(ValueError):
        BadExclude(user)

def test_dateformat_option(user):
    fmt = '%Y-%m'

    class DateFormatSchema(Schema):
        updated = fields.DateTime("%m-%d")

        class Meta:
            fields = ('created', 'updated')
            dateformat = fmt
    serialized = DateFormatSchema(user)
    assert serialized.data['created'] == user.created.strftime(fmt)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_default_dateformat(user):
    class DateFormatSchema(Schema):
        updated = fields.DateTime(format="%m-%d")

        class Meta:
            fields = ('created', 'updated')
    serialized = DateFormatSchema(user)
    assert serialized.data['created'] == utils.isoformat(user.created)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_inherit_meta(user):
    class InheritedMetaSchema(UserMetaSchema):
        pass
    result = InheritedMetaSchema(user).data
    expected = UserMetaSchema(user).data
    assert result == expected

def test_additional(user):
    s = UserAdditionalSchema(user)
    assert s.data['lowername'] == user.name.lower()
    assert s.data['name'] == user.name

def test_cant_set_both_additional_and_fields(user):
    class BadSchema(Schema):
        name = fields.String()

        class Meta:
            fields = ("name", 'email')
            additional = ('email', 'homepage')
    with pytest.raises(ValueError):
        BadSchema(user)

def test_serializing_none_meta():
    s = UserMetaSchema(None)
    # Since meta fields are used, defaults to None
    assert s.data['name'] is None
    assert s.data['email'] is None


class CustomError(Exception):
    pass

class MySchema(Schema):
    name = fields.String()
    email = fields.Email()

class MySchema2(Schema):
    homepage = fields.URL()

def test_dump_with_custom_error_handler(user):
    @MySchema.error_handler
    def handle_errors(serializer, errors, obj):
        assert isinstance(serializer, MySchema)
        assert 'email' in errors
        assert isinstance(obj, User)
        raise CustomError('Something bad happened')

    user.email = 'bademail'
    with pytest.raises(CustomError):
        MySchema().dump(user)

    user.email = 'monty@python.org'
    assert MySchema(user).data

def test_load_with_custom_error_handler():
    @MySchema.error_handler
    def handle_errors(serializer, errors, data):
        assert isinstance(serializer, MySchema)
        assert 'email' in errors
        assert isinstance(data, dict)
        raise CustomError('Something bad happened')
    with pytest.raises(CustomError):
        MySchema().load({'email': 'invalid'})

def test_multiple_serializers_with_same_error_handler(user):

    @MySchema.error_handler
    @MySchema2.error_handler
    def handle_errors(serializer, errors, obj):
        raise CustomError('Something bad happened')
    user.email = 'bademail'
    user.homepage = 'foo'
    with pytest.raises(CustomError):
        MySchema().dump(user)
    with pytest.raises(CustomError):
        MySchema2().dump(user)

def test_setting_error_handler_class_attribute(user):
    def handle_errors(serializer, errors, obj):
        raise CustomError('Something bad happened')

    class ErrorSchema(Schema):
        email = fields.Email()
        __error_handler__ = handle_errors

    class ErrorSchemaSub(ErrorSchema):
        pass

    user.email = 'invalid'

    ser = ErrorSchema()
    with pytest.raises(CustomError):
        ser.dump(user)

    subser = ErrorSchemaSub()
    with pytest.raises(CustomError):
        subser.dump(user)


def test_serializer_with_custom_data_handler(user):
    class CallbackSchema(Schema):
        name = fields.String()

    @CallbackSchema.data_handler
    def add_meaning(serializer, data, obj):
        data['meaning'] = 42
        return data

    ser = CallbackSchema()
    data, _ = ser.dump(user)
    assert data['meaning'] == 42

def test_serializer_with_multiple_data_handlers(user):
    class CallbackSchema2(Schema):
        name = fields.String()

    @CallbackSchema2.data_handler
    def add_meaning(serializer, data, obj):
        data['meaning'] = 42
        return data

    @CallbackSchema2.data_handler
    def upper_name(serializer, data, obj):
        data['name'] = data['name'].upper()
        return data

    ser = CallbackSchema2()
    data, _ = ser.dump(user)
    assert data['meaning'] == 42
    assert data['name'] == user.name.upper()

def test_setting_data_handlers_class_attribute(user):
    def add_meaning(serializer, data, obj):
        data['meaning'] = 42
        return data

    class CallbackSchema3(Schema):
        __data_handlers__ = [add_meaning]

        name = fields.String()

    ser = CallbackSchema3()
    data, _ = ser.dump(user)
    assert data['meaning'] == 42

def test_root_data_handler(user):
    class RootSchema(Schema):
        NAME = 'user'

        name = fields.String()

    @RootSchema.data_handler
    def add_root(serializer, data, obj):
        return {
            serializer.NAME: data
        }

    s = RootSchema()
    data, _ = s.dump(user)
    assert data['user']['name'] == user.name

def test_serializer_repr():
    class MySchema(Schema):
        name = fields.String()

    ser = MySchema(many=True, strict=True)
    rep = repr(ser)
    assert 'MySchema' in rep
    assert 'strict=True' in rep
    assert 'many=True' in rep


class TestNestedSchema:

    def setup_method(self, method):
        self.user = User(name="Monty", age=81)
        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        self.blog = Blog("Monty's blog", user=self.user, categories=["humor", "violence"],
                         collaborators=[col1, col2])

    def test_flat_nested(self):
        class FlatBlogSchema(Schema):
            name = fields.String()
            user = fields.Nested(UserSchema, only='name')
            collaborators = fields.Nested(UserSchema, only='name', many=True)
        s = FlatBlogSchema()
        data, _ = s.dump(self.blog)
        assert data['user'] == self.blog.user.name
        for i, name in enumerate(data['collaborators']):
            assert name == self.blog.collaborators[i].name

    def test_flat_nested2(self):
        class FlatBlogSchema(Schema):
            name = fields.String()
            collaborators = fields.Nested(UserSchema, many=True, only='uid')

        s = FlatBlogSchema()
        data, _ = s.dump(self.blog)
        assert data['collaborators'][0] == str(self.blog.collaborators[0].uid)

    def test_required_nested_field(self):
        class BlogRequiredSchema(Schema):
            user = fields.Nested(UserSchema, required=True)

        b = Blog('Authorless blog', user=None)
        _, errs = BlogRequiredSchema().dump(b)
        assert 'user' in errs
        assert 'required' in errs['user']

    def test_nested_default(self):
        class BlogDefaultSchema(Schema):
            user = fields.Nested(UserSchema, default=0)

        b = Blog('Just the default blog', user=None)
        data, _ = BlogDefaultSchema().dump(b)
        assert data['user'] == 0

    def test_nested_none_default(self):
        class BlogDefaultSchema(Schema):
            user = fields.Nested(UserSchema, default=None)

        b = Blog('Just the default blog', user=None)
        data, _ = BlogDefaultSchema().dump(b)
        assert data['user'] is None

    def test_nested(self):
        blog_serializer = BlogSchema()
        serialized_blog, _ = blog_serializer.dump(self.blog)
        user_serializer = UserSchema()
        serialized_user, _ = user_serializer.dump(self.user)
        assert serialized_blog['user'] == serialized_user

    def test_nested_many_fields(self):
        serialized_blog, _ = BlogSchema().dump(self.blog)
        expected = [UserSchema().dump(col)[0] for col in self.blog.collaborators]
        assert serialized_blog['collaborators'] == expected

    def test_nested_meta_many(self):
        serialized_blog = BlogUserMetaSchema().dump(self.blog)[0]
        assert len(serialized_blog['collaborators']) == 2
        expected = [UserMetaSchema().dump(col)[0] for col in self.blog.collaborators]
        assert serialized_blog['collaborators'] == expected

    def test_nested_only(self):
        col1 = User(name="Mick", age=123, id_="abc")
        col2 = User(name="Keith", age=456, id_="def")
        self.blog.collaborators = [col1, col2]
        serialized_blog = BlogOnlySchema().dump(self.blog)[0]
        assert serialized_blog['collaborators'] == [{"id": col1.id}, {"id": col2.id}]

    def test_exclude(self):
        serialized = BlogSchemaExclude().dump(self.blog)[0]
        assert "uppername" not in serialized['user'].keys()

    def test_only_takes_precedence_over_exclude(self):
        serialized = BlogSchemaOnlyExclude().dump(self.blog)[0]
        assert serialized['user']['name'] == self.user.name

    def test_list_field(self):
        serialized = BlogSchema().dump(self.blog)[0]
        assert serialized['categories'] == ["humor", "violence"]

    def test_nested_errors(self):
        invalid_user = User("Monty", email="foo")
        blog = Blog("Monty's blog", user=invalid_user)
        serialized_blog, errors = BlogSchema().dump(blog)
        assert "email" in errors['user']
        expected_msg = "\"{0}\" is not a valid email address.".format(invalid_user.email)
        assert errors['user']['email'] == expected_msg
        # No problems with collaborators
        assert "collaborators" not in errors

    def test_nested_method_field(self):
        data = BlogSchema().dump(self.blog)[0]
        assert data['user']['is_old']
        assert data['collaborators'][0]['is_old']

    def test_nested_function_field(self):
        data = BlogSchema().dump(self.blog)[0]
        assert data['user']['lowername'] == self.user.name.lower()
        expected = self.blog.collaborators[0].name.lower()
        assert data['collaborators'][0]['lowername'] == expected

    def test_nested_prefixed_field(self):
        data = BlogSchemaPrefixedUser().dump(self.blog)[0]
        assert data['user']['usr_name'] == self.user.name
        assert data['user']['usr_lowername'] == self.user.name.lower()

    def test_nested_prefixed_many_field(self):
        data = BlogSchemaPrefixedUser().dump(self.blog)[0]
        assert data['collaborators'][0]['usr_name'] == self.blog.collaborators[0].name

    def test_invalid_float_field(self):
        user = User("Joe", age="1b2")
        _, errors = UserSchema().dump(user)
        assert "age" in errors

    def test_serializer_meta_with_nested_fields(self):
        data = BlogSchemaMeta().dump(self.blog)[0]
        assert data['title'] == self.blog.title
        assert data['user'] == UserSchema(self.user).data
        assert data['collaborators'] == [UserSchema(c).data
                                               for c in self.blog.collaborators]
        assert data['categories'] == self.blog.categories

    def test_serializer_with_nested_meta_fields(self):
        # Schema has user = fields.Nested(UserMetaSerializer)
        s = BlogUserMetaSchema(self.blog)
        assert s.data['user'] == UserMetaSchema(self.blog.user).data

    def test_nested_fields_must_be_passed_a_serializer(self):
        class BadNestedFieldSchema(BlogSchema):
            user = fields.Nested(fields.String)
        with pytest.raises(ValueError):
            BadNestedFieldSchema().dump(self.blog)


class TestSelfReference:

    def setup_method(self, method):
        self.employer = User(name="Joe", age=59)
        self.user = User(name="Tom", employer=self.employer, age=28)

    def test_nesting_serializer_within_itself(self):
        class SelfSchema(Schema):
            name = fields.String()
            age = fields.Integer()
            employer = fields.Nested('self', exclude=('employer', ))

        data, errors = SelfSchema().dump(self.user)
        assert not errors
        assert data['name'] == self.user.name
        assert data['employer']['name'] == self.employer.name
        assert data['employer']['age'] == self.employer.age

    def test_nesting_within_itself_meta(self):
        class SelfSchema(Schema):
            employer = fields.Nested("self", exclude=('employer', ))

            class Meta:
                additional = ('name', 'age')

        data, errors = SelfSchema().dump(self.user)
        assert not errors
        assert data['name'] == self.user.name
        assert data['age'] == self.user.age
        assert data['employer']['name'] == self.employer.name
        assert data['employer']['age'] == self.employer.age

    def test_nested_self_with_only_param(self):
        class SelfSchema(Schema):
            employer = fields.Nested('self', only=('name', ))

            class Meta:
                fields = ('name', 'employer')

        data = SelfSchema().dump(self.user)[0]
        assert data['name'] == self.user.name
        assert data['employer']['name'] == self.employer.name
        assert 'age' not in data['employer']

    def test_multiple_nested_self_fields(self):
        class MultipleSelfSchema(Schema):
            emp = fields.Nested('self', only='name', attribute='employer')
            rels = fields.Nested('self', only='name',
                                    many=True, attribute='relatives')

            class Meta:
                fields = ('name', 'emp', 'rels')

        schema = MultipleSelfSchema()
        self.user.relatives = [User(name="Bar", age=12), User(name='Baz', age=34)]
        data, errors = schema.dump(self.user)
        assert not errors
        assert len(data['rels']) == len(self.user.relatives)
        relative = data['rels'][0]
        assert relative == self.user.relatives[0].name

    def test_nested_many(self):
        class SelfManySchema(Schema):
            relatives = fields.Nested('self', many=True)

            class Meta:
                additional = ('name', 'age')

        person = User(name='Foo')
        person.relatives = [User(name="Bar", age=12), User(name='Baz', age=34)]
        data = SelfManySchema().dump(person)[0]
        assert data['name'] == person.name
        assert len(data['relatives']) == len(person.relatives)
        assert data['relatives'][0]['name'] == person.relatives[0].name
        assert data['relatives'][0]['age'] == person.relatives[0].age


def test_serialization_with_required_field():
    class RequiredUserSchema(Schema):
        name = fields.String(required=True)

    user = User(name=None)
    data, errors = RequiredUserSchema().dump(user)
    assert 'name' in errors
    assert errors['name'] == 'Missing data for required field.'


def test_serialization_with_required_field_and_custom_validator():
    class RequiredGenderSchema(Schema):
        gender = fields.String(required=True,
                               validate=lambda x: x.lower() == 'f' or x.lower() == 'm',
                               error="Gender must be 'f' or 'm'.")

    user = dict(gender=None)
    data, errors = RequiredGenderSchema().dump(user)
    assert errors
    assert 'gender' in errors
    assert errors['gender'] == "Missing data for required field."

    user = dict(gender='Unkown')
    s = RequiredGenderSchema(user)
    assert s.is_valid() is False
    assert 'gender' in s.errors
    assert s.errors['gender'] == "Gender must be 'f' or 'm'."


class UserContextSchema(Schema):
    is_owner = fields.Method('get_is_owner')
    is_collab = fields.Function(lambda user, ctx: user in ctx['blog'])

    def get_is_owner(self, user, context):
        return context['blog'].user.name == user.name


class TestContext:

    def test_context_method(self):
        owner = User('Joe')
        blog = Blog(title='Joe Blog', user=owner)
        context = {'blog': blog}
        serializer = UserContextSchema()
        serializer.context = context
        data = serializer.dump(owner)[0]
        assert data['is_owner'] is True
        nonowner = User('Fred')
        data = serializer.dump(nonowner)[0]
        assert data['is_owner'] is False

    def test_context_method_function(self):
        owner = User('Fred')
        blog = Blog('Killer Queen', user=owner)
        collab = User('Brian')
        blog.collaborators.append(collab)
        context = {'blog': blog}
        serializer = UserContextSchema()
        serializer.context = context
        data = serializer.dump(collab)[0]
        assert data['is_collab'] is True
        noncollab = User('Foo')
        data = serializer.dump(noncollab)[0]
        assert data['is_collab'] is False

    def test_method_field_raises_error_when_context_not_available(self):
        # serializer that only has a method field
        class UserMethodContextSchema(Schema):
            is_owner = fields.Method('get_is_owner')

            def get_is_owner(self, user, context):
                return context['blog'].user.name == user.name
        owner = User('Joe')
        serializer = UserContextSchema(strict=True)
        serializer.context = None
        with pytest.raises(MarshallingError) as excinfo:
            serializer.dump(owner)

        msg = 'No context available for Method field {0!r}'.format('is_owner')
        assert msg in str(excinfo)

    def test_function_field_raises_error_when_context_not_available(self):
        # only has a function field
        class UserFunctionContextSchema(Schema):
            is_collab = fields.Function(lambda user, ctx: user in ctx['blog'])

        owner = User('Joe')
        serializer = UserFunctionContextSchema(strict=True)
        # no context
        serializer.context = None
        with pytest.raises(MarshallingError) as excinfo:
            serializer.dump(owner)
        msg = 'No context available for Function field {0!r}'.format('is_collab')
        assert msg in str(excinfo)

    def test_fields_context(self):
        class CSchema(Schema):
            name = fields.String()

        ser = CSchema()
        ser.context['foo'] = 42

        assert ser.fields['name'].context == {'foo': 42}

    def test_nested_fields_inherit_context(self):
        class InnerSchema(Schema):
            likes_bikes = fields.Function(lambda obj, ctx: 'bikes' in ctx['info'])

        class CSchema(Schema):
            inner = fields.Nested(InnerSchema)

        ser = CSchema(strict=True)

        ser.context['info'] = 'i like bikes'
        obj = {
            'inner': {}
        }
        result = ser.dump(obj)
        assert result.data['inner']['likes_bikes'] is True


def raise_marshalling_value_error():
    try:
        raise ValueError('Foo bar')
    except ValueError as error:
        raise MarshallingError(error)

class TestMarshallingError:

    def test_saves_underlying_exception(self):
        with pytest.raises(MarshallingError) as excinfo:
            raise_marshalling_value_error()
        assert 'Foo bar' in str(excinfo)
        error = excinfo.value
        assert isinstance(error.underlying_exception, ValueError)


def test_error_gets_raised_if_many_is_omitted(user):
    class BadSchema(Schema):
        # forgot to set many=True
        class Meta:
            fields = ('name', 'relatives')
        relatives = fields.Nested(UserSchema)

    user.relatives = [User('Joe'), User('Mike')]

    with pytest.raises(TypeError) as excinfo:
        BadSchema().dump(user)
        # Exception includes message about setting many argument
        assert 'many=True' in str(excinfo)

def test_serializer_can_specify_nested_object_as_attribute(blog):
    class BlogUsernameSchema(Schema):
        author_name = fields.String(attribute='user.name')
    ser = BlogUsernameSchema()
    result = ser.dump(blog)
    assert result.data['author_name'] == blog.user.name
