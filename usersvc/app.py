from cornice.resource import resource
from cornice.resource import view
from cornice.validators import colander_body_validator
from google.cloud import firestore
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPCreated
from pyramid.httpexceptions import HTTPNotAcceptable
from pyramid.httpexceptions import HTTPConflict
import colander


def stringish():
    return colander.SchemaNode(colander.String())


class UserSchema(colander.MappingSchema):
    userid = stringish()
    first_name = stringish()
    last_name = stringish()
    groups = colander.SequenceSchema(stringish())


class GroupSchema(colander.MappingSchema):
    name = stringish()


@resource(collection_path="/users", path="/users/{id}")
class User(object):
    """
    Representation of a user
    """
    def __init__(self, request, context=None):
        self.db = request.db
        self.request = request
        self.context = context

    def get_user_ref(self, userid):
        dref = self.db\
          .collection(u'users')\
          .document(userid)
        return dref

    @property
    def groups(self):
        gref = self.db.collection(u'groups')
        return {g.id for g in gref.stream()}

    def set_user_data(self, userid, new_data):
        dref = self.db\
          .collection(u'users')\
          .document(userid)
        dref.create(new_data)

    def groups_exist(self, request, **kwargs):
        user = self.request.json_body
        groups = user.get('groups', [])
        bad_groups = [group for group in groups \
                      if group not in self.groups]
        if bad_groups:
            request.errors.add("body",
                              "groups",
                              "invalid groups: %s" % ",".join(bad_groups))

    @view(schema=UserSchema(),
          validators=(colander_body_validator, 'groups_exist'))
    def collection_post(self):
        user = self.request.json_body
        uid = user['userid']
        dref = self.get_user_ref(uid)
        try:
            dref.create(user)
        except Exception as e:
            # @@ move to validator???
            raise HTTPConflict("User %s Exists" % uid)
        self.request.response.status_code = 201
        return True

    @property
    def user_data(self):
        # @@ better as a validator?
        # @@ add checking for empty id (if server does not handle)
        uid = self.request.matchdict.get('id', False)
        dref = self.get_user_ref(uid)
        snap = dref.get()
        if snap.exists:
            return snap.to_dict()
        raise HTTPNotFound

    def get(self):
        return self.user_data

    @view(schema=UserSchema(),
          validators=(colander_body_validator, 'groups_exist'))
    def put(self):
        user = self.user_data
        new_data = self.request.json_body
        theuid = user['userid']

        #@@ exists validator??
        assert theuid == new_data['userid']

        user.update(new_data)
        dref = self.get_user_ref(user['userid'])
        dref.set(user)
        self.request.response.status_code = 202
        return True

    def delete(self):
        uid = self.request.matchdict['id']
        self.get_user_ref(uid).delete()
        self.request.response.status_code = 204
        return True


@resource(collection_path="/groups", path="/groups/{id}")
class Group(object):
    """
    Representation of a collection of ugrefsers
    """
    def __init__(self, request, context=None):
        self.db = request.db
        self.request = request
        self.context = context

    @view(schema=GroupSchema(),
          validators=(colander_body_validator, 'group_must_not_exist'))
    def collection_post(self):
        gdata = self.request.json_body
        guid = gdata['name']
        gref = self.get_group_ref(guid)
        try:
            gref.create(dict(name=guid))
        except Exception as e:
            raise HTTPConflict("Group %s Exists" % guid)
        self.request.response.status_code = 201
        return True

    def get_user_data(self, userid):
        uref = self.get_user_ref(userid)
        udata = uref.get().to_dict()
        return udata, uref

    @view(validators=('group_exists'))
    def put(self):
        guid = self.request.matchdict.get('id')
        snap = self.get_group_ref(guid).get()
        for userid in self.request.json_body['users']:
            udata, uref = self.get_user_data(userid)
            gs = set(udata['groups'])
            gs.add(guid)
            udata['groups'] = list(gs)
            uref.set(udata)
        self.request.response.status_code = 202

    @view(validators=('group_exists'))
    def get(self):
        guid = self.request.matchdict['id']
        uids = self.users_by_group(guid)
        return uids

    @view(validators=('group_exists',))
    def delete(self):
        """
        Deletes canonical entry and then all references in user collection
        """
        guid = self.request.matchdict['id']
        gref = self.get_group_ref(guid)
        gref.delete()

        # clean up users
        query = self.users_by_group_query(guid)
        for snap in query.stream():
            user_data = snap.to_dict()
            groups = user_data['groups']
            groups.remove(guid)
            snap.reference.update(dict(groups=groups))
        self.request.response.status_code = 204

    def get_group_ref(self, group_name):
        dref = self.db \
          .collection(u'groups')\
          .document(group_name)
        return dref

    def users_by_group_query(self, guid):
        cref = self.db.collection(u'users')
        query = cref.where(u'groups', u'array_contains', guid)
        return query

    def users_by_group(self, guid):
        query = self.users_by_group_query(guid)
        uids = [x.to_dict().get('userid') for x in query.stream()]
        return uids

    def get_group_snapshot(self, guid):
        snap = self.get_group_ref(guid).get()
        return snap

    def group_exists(self, request, **kw):
        guid = self.request.matchdict['id']
        snap = self.get_group_snapshot(guid)
        if snap.exists:
            return True
        self.request.errors.add('body', 'group', 'does not exist')
        self.request.errors.status = 404
        return False

    def get_user_ref(self, userid):
        dref = self.db\
          .collection(u'users')\
          .document(userid)
        return dref

    def group_must_not_exist(self, request, **kw):
        guid = self.request.json_body.get('name')
        snap = self.get_group_snapshot(guid)

        if snap.exists:
            self.request.errors.add('body', 'group', 'group exists')
            self.request.errors.status = 403
            return False
        return True


def firestore_tween_ctor(handler, registry):
    """
    annotate request w/ db handle
    """
    firestore_client = firestore.Client()
    def provide_db(request):
        request.db = firestore_client
        return handler(request)
    return provide_db


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("usersvc.app")
    db_tween = settings.get('db_tween', "usersvc.app.firestore_tween_ctor")
    config.add_tween(db_tween)
    return config.make_wsgi_app()
