import hashlib
import urllib2
import json
import logging
from urlparse import urljoin
from django.conf import settings
from django.http import QueryDict
from pymongo import MongoClient

from idmap.plugin import Plugin

logger = logging.getLogger(__name__)


def hash_md5(local_id, salt):
    return hashlib.md5(local_id + salt).hexdigest()


class RemoteIdProvider(Plugin):
    name = 'Remote Id Provider'

    def get_needs(self):
        return ['user_id']

    def get_provides(self):
        return ['user_id', 'remote_id']

    def get_remote_id(self, user_ids):
        ret = {}
        for user_id in user_ids:
            ret[user_id] = hash_md5(user_id, settings.HASH_SALT)

        return ret

    def load(self, **params):
        user_ids = params.get('user_id', [])

        return [{'user_id': user_id, 'remote_id': hash_md5(user_id, settings.HASH_SALT)} for user_id in user_ids]


class MongoProvider(Plugin):
    name = "Mongo Backend Provider"

    settings = {'MONGO_HOST': 'localhost', 'MONGO_PORT': 27017, 'MONGO_DATABASE': 'test'}

    def __init__(self):
        self.client = None
        self.db = None

    def load_settings(self):
        self.client = MongoClient(
            settings.PROVIDER[type(self).__name__]['MONGO_HOST'],
            int(settings.PROVIDER[type(self).__name__]['MONGO_PORT'])
        )
        self.db = self.client[settings.PROVIDER[type(self).__name__]['MONGO_DATABASE']]

    def get_needs(self):
        raise NotImplementedError

    def get_provides(self):
        raise NotImplementedError


class UserInfoProvider(MongoProvider):
    name = "UBC User Info Provider"

    def get_needs(self):
        return ['user_id', 'remote_id', 'student_number', 'employee_number']

    def get_provides(self):
        return ['user_id', 'first_name', 'last_name', 'email', 'remote_id',
                'student_number', 'employee_number']

    def get_user_id(self, user_dict):
        return user_dict['ubcEduCwlPUID']
        # return {user_id: user['ubcEduCwlPUID'] if 'ubcEduCwlPUID' in user else None
        #         for user_id, user in self.users.iteritems() if user_id in user_ids}

    def get_first_name(self, user_dict):
        return user_dict['displayName'].split(',')[1].strip() if 'displayName' in user_dict else None

    def get_last_name(self, user_dict):
        return user_dict['displayName'].split(',')[0].strip() if 'displayName' in user_dict else None

    def get_remote_id(self, user_dict):
        return user_dict['edx_id']

    def get_email(self, user_dict):
        return user_dict['mail'] if 'mail' in user_dict else None

    def get_student_number(self, user_dict):
        return user_dict['ubcEduStudentNumber'] if 'ubcEduStudentNumber' in user_dict else None

    def get_employee_number(self, user_dict):
        return user_dict['employeeNumber'] if 'employeeNumber' in user_dict else None


    # def get_first_name(self, user_ids):
    #     self.load(user_ids=user_ids)
    #     return {user_id: user['displayName'].split(',')[1].strip() if 'displayName' in user else None
    #             for user_id, user in self.users.iteritems()
    #             if user_id in user_ids}
    #
    # def get_last_name(self, user_ids):
    #     self.load(user_ids=user_ids)
    #     return {user_id: user['displayName'].split(',')[0].strip() if 'displayName' in user else None
    #             for user_id, user in self.users.iteritems()
    #             if user_id in user_ids}
    #
    # def get_email(self, user_ids):
    #     self.load(user_ids=user_ids)
    #     return {user_id: user['mail'] if 'mail' in user else None
    #             for user_id, user in self.users.iteritems()
    #             if user_id in user_ids}

    def load(self, **params):
        super(UserInfoProvider, self).load()
        field_mapping = {
            'user_id': 'ubcEduCwlPUID',
            'remote_id': 'edx_id',
            'student_number': 'ubcEduStudentNumber',
            'employee_number': 'employeeNumber'
        }

        # query mongo to get user info

        condition = []
        for field in field_mapping.keys():
            values = params.get(field, [])
            if values:
                condition.append({field_mapping[field]: {'$in': values}})

        cursor = self.db.users.find({'$or': condition})

        users = []
        for result in cursor:
            users.append({key: getattr(self, 'get_' + key)(result) for key in self.get_provides()})

        return users


class EdxUsernameProvider(Plugin):
    name = "Edx Username Provider"
    # this is cached between requests. may not be what we want.

    def get_needs(self):
        return ['edx_username', 'remote_id']

    def get_provides(self):
        return ['edx_username', 'remote_id']

    def get_edx_username(self, user_dict):
        return user_dict['username'] if 'username' in user_dict else None

    def get_remote_id(self, user_dict):
        return user_dict['remote_id'] if 'remote_id' in user_dict else None

    def load(self, **params):
        edx_usernames = params.get('edx_username', [])
        remote_ids = params.get('remote_id', [])
        query = QueryDict(mutable=True)
        query.setlist('remote_id', remote_ids)
        query.setlist('username', edx_usernames)
        if not query.urlencode():
            # nothing to query
            return []
        headers = {'Authorization': 'Bearer {}'.format(settings.EDX_ACCESS_TOKEN)}
        url = urljoin(settings.EDX_SERVER, settings.EDX_MAPPING_ENDPOINT)
        req = urllib2.Request(url + '?' + query.urlencode(), None, headers)
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            raise RuntimeError('Failed to contact EdX API. {}'.format(e.reason))
        data = json.load(response)

        users = []
        for user in data['results']:
            users.append({key: getattr(self, 'get_' + key)(user) for key in self.get_provides()})

        return users
