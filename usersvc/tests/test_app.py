from google.cloud import firestore
from pytest import fixture
from unittest import mock
from unittest.mock import Mock
from unittest.mock import PropertyMock
from unittest.mock import patch
from usersvc.app import main
from webtest import TestApp
import pytest

dbmock = mock.Mock(firestore.Client)

def mock_firestore_tween(handler, registry):
    def provide_db(request):
        request.db = dbmock
        response = handler(request)
        return response
    return provide_db

@fixture
def app():
    settings = dict(db_tween='usersvc.tests.test_app.mock_firestore_tween')
    app = TestApp(main({}, **settings))
    return app

def test_user_get_notfound(app):
    dbmock.collection().document().get().exists = False
    app.get('/users/bob', status=404)

def test_user_get_found(app):
    dbmock.collection().document().get().exists = True
    dbmock.collection().document().get().to_dict.return_value = dict(foo=True)
    res = app.get('/users/bob', status=200)
    assert res.json == {'foo': True}

user_record = dict(userid="sue",
                   first_name="sue",
                   last_name="suesue",
                   groups=['admin'])

broken_record = dict(username="sue",
                     fist_name="sue",
                     lat_name="suesue",
                     groups=['admin'])

def test_post_create_user(app):
    with patch("usersvc.app.User.groups", new_callable=PropertyMock) as groups:
        groups.return_value = set(['red', 'green', 'admin'])
        app.post_json('/users', user_record, status=201)

def test_post_create_user_schema_violation(app):
    with patch("usersvc.app.User.groups", new_callable=PropertyMock) as groups:
        groups.return_value = set(['red', 'green', 'admin'])
        res = app.post_json('/users', broken_record, status=400)

def test_post_create_user_group_violation(app):
    with patch("usersvc.app.User.groups", new_callable=PropertyMock) as groups:
        groups.return_value = set(['not admin'])
        app.post_json('/users', user_record, status=400)

def test_put_update_user(app):
    new_record = user_record.copy()
    new_record['groups'] = ['green']
    with patch("usersvc.app.User.groups", new_callable=PropertyMock) as groups,\
        patch("usersvc.app.User.user_data", new_callable=PropertyMock) as userdata:
        groups.return_value = set(['red', 'green', 'admin'])
        userdata.return_value = user_record
        app.put_json('/users/sue', new_record, status=202)

def test_user_delete(app):
    new_record = user_record.copy()
    new_record['groups'] = ['green']
    with patch("usersvc.app.User.get_user_ref") as uref:
        res = app.delete('/users/sue', status=204)
        assert uref().delete.called

def test_group_get_no_group(app):
    with patch("usersvc.app.Group.users_by_group_query") as ubgq,\
      patch("usersvc.app.Group.get_group_snapshot") as gsnap:
        gsnap().exists = False
        ubgq.stream.return_value = []
        app.get('/groups/admin', status=404)

def test_group_create_collision(app):
    with patch("usersvc.app.Group.group_must_not_exist") as gmne:
        gmne.return_value = True
        app.post_json('/groups', dict(name="admin"), status=201)

def test_group_create_success(app):
    app.post_json('/groups', dict(name="admin"), status=403)

def test_group_manage(app):
    dbmock.collection()\
      .document()\
      .get()\
      .to_dict \
      .return_value = user_record
    app.put_json('/groups/admin', dict(users=["sue"]), status=202)

def test_group_get(app):
    with patch("usersvc.app.Group.users_by_group_query") as ubgq:
        mockdoc = Mock()
        mockdoc.to_dict.return_value = dict(userid="sue")
        ubgq.stream.return_value = mockdoc,
        app.get('/groups/admin', status=200)

def test_group_delete(app):
    with patch("usersvc.app.Group.users_by_group_query") as ubgq:
        mockdoc = Mock()
        mockdoc.to_dict.return_value = dict(userid="sue")
        ubgq.stream.return_value = mockdoc,
        app.delete('/groups/admin', status=204)
