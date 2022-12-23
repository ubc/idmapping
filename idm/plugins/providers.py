import json
import logging
import urllib2
from urlparse import urljoin

from django.conf import settings
from django.http import QueryDict

from idm.plugins.manager import BaseProvider

logger = logging.getLogger(__name__)

# def hash_md5(local_id, salt):
#     return hashlib.md5(local_id + salt).hexdigest()


# class RemoteIdProvider(BaseProvider):
#     name = 'Remote Id Provider'
#
#     def get_needs(self):
#         return ['user_id']
#
#     def get_provides(self):
#         return ['user_id', 'remote_id']
#
#     def get_remote_id(self, user_ids):
#         ret = {}
#         for user_id in user_ids:
#             ret[user_id] = hash_md5(user_id, settings.HASH_SALT)
#
#         return ret
#
#     def load(self, **params):
#         user_ids = params.get('user_id', [])
#
#         return [{'user_id': user_id, 'remote_id': hash_md5(user_id, settings.HASH_SALT)} for user_id in user_ids]


class MongoProvider(BaseProvider):
    name = "Mongo Backend Provider"

    settings = {'MONGO_HOST': 'localhost:27017', 'MONGO_DATABASE': 'test', 'MONGO_USER': None, 'MONGO_PASS': None}

    def __init__(self):
        self.client = None
        self.db = None

    def load_settings(self):
        from mongo import mongo_client, mongo_db
        self.client = mongo_client
        self.db = mongo_db


class UserInfoProvider(MongoProvider):
    name = "UBC User Info Provider"

    def get_needs(self):
        return ['user_id', 'cwl', 'remote_id', 'student_number', 'employee_number', 'email']

    def get_provides(self):
        return ['user_id', 'cwl', 'first_name', 'last_name', 'email', 'remote_id',
                'student_number', 'employee_number']

    def get_user_id(self, user_dict):
        return user_dict['ubcEduCwlPUID']
        # return {user_id: user['ubcEduCwlPUID'] if 'ubcEduCwlPUID' in user else None
        #         for user_id, user in self.users.iteritems() if user_id in user_ids}

    def get_cwl(self, user_dict):
        return user_dict['uid']

    def get_first_name(self, user_dict):
        return user_dict['cn'].split(' ')[0].strip() if 'cn' in user_dict else None

    def get_last_name(self, user_dict):
        return user_dict['cn'].split(' ')[1].strip() if 'cn' in user_dict else None

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
            'employee_number': 'employeeNumber',
            'email': 'mail',
        }

        # query mongo to get user info
        condition = []
        for field in field_mapping.keys():
            values = params.get(field, [])
            if values:
                condition.append({field_mapping[field]: {'$in': values}})

        users = []
        if condition:
            cursor = self.db.users.find({'$or': condition})

            for result in cursor:
                users.append({key: getattr(self, 'get_' + key)(result) for key in self.get_provides()})

        return users


class EdxUsernameProvider(BaseProvider):
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
        # edx is checking User-Agent, default urllib UA will result "forbidden" error
        headers = {'Authorization': 'JWT {}'.format(settings.EDX_ACCESS_TOKEN),
                   'Accept': '*/*', 'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'}
        url = urljoin(settings.EDX_SERVER, settings.EDX_MAPPING_ENDPOINT)
        req = urllib2.Request(url + '?' + query.urlencode(), None, headers)
        # handler = urllib2.HTTPSHandler(debuglevel=1)
        # opener = urllib2.build_opener(handler)
        # urllib2.install_opener(opener)
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            raise RuntimeError('Failed to contact EdX API. {}'.format(e.reason))
        data = json.load(response)

        users = []
        for user in data['results']:
            users.append({key: getattr(self, 'get_' + key)(user) for key in self.get_provides()})

        return users
