import unittest
import urllib2

from ddt import ddt, unpack, data
from django.test import override_settings
from mock import patch, MagicMock
from six import StringIO

from idm.plugins.providers import MongoProvider, UserInfoProvider, EdxUsernameProvider


class MongoProviderTest(unittest.TestCase):
    @override_settings(
        PROVIDER={'MongoProvider': {'MONGO_HOST': 'localhost', 'MONGO_PORT': 27017, 'MONGO_DATABASE': 'test'}}
    )
    def test_load(self):
        provider = MongoProvider()
        provider.load()
        from pymongo import MongoClient
        self.assertIsInstance(provider.client, MongoClient)
        self.assertIsNotNone(provider.db)


@ddt
class UserInfoProviderTest(unittest.TestCase):
    @patch('idm.plugins.providers.MongoClient')
    @data(
        # empty result from db
        ({'user_id': ['test']},
         {'$or': [{'ubcEduCwlPUID': {'$in': ['test']}}]},
         [],
         []),
        # one result from db
        ({'user_id': ['test', 'test1']},
         {'$or': [{'ubcEduCwlPUID': {'$in': ['test', 'test1']}}]},
         [{'ubcEduCwlPUID': 'test', 'cn': 'Test Joe', 'uid': 'test', 'edx_id': 'test'}],
         [{'first_name': 'Test', 'last_name': 'Joe', 'user_id': 'test', 'employee_number': None,
             'remote_id': 'test', 'cwl': 'test', 'student_number': None, 'email': None}]),
        # multiple search criteria
        ({'user_id': ['test'], 'email': ['a@a.com']},
         {'$or': [{'ubcEduCwlPUID': {'$in': ['test']}}, {'mail': {'$in': ['a@a.com']}}]},
         [{'ubcEduCwlPUID': 'test', 'cn': 'Test Joe', 'uid': 'test', 'edx_id': 'test'}],
         [{'first_name': 'Test', 'last_name': 'Joe', 'user_id': 'test', 'employee_number': None,
           'remote_id': 'test', 'cwl': 'test', 'student_number': None, 'email': None}]),
    )
    @unpack
    def test_load(self, load_params, condition, find_return, expect_users, mock_client):
        mock_db = MagicMock(name='mock_db')
        mock_db.users = MagicMock(name='mock_collection')
        mock_db.users.find.return_value = find_return
        mock_client.return_value.__getitem__.side_effect = lambda _: mock_db
        provider = UserInfoProvider()
        users = provider.load(**load_params)

        mock_client.assert_called_once_with('localhost', 27017)
        mock_db.users.find.assert_called_once_with(condition)
        self.assertListEqual(users, expect_users)


@ddt
class EdxUsernameProviderTest(unittest.TestCase):
    @override_settings(EDX_ACCESS_TOKEN='token', EDX_SERVER='http://edx.org', EDX_MAPPING_ENDPOINT='/api/user')
    @patch('idm.plugins.providers.urllib2.urlopen')
    @patch('idm.plugins.providers.urllib2.Request')
    @data(
        # empty query
        ({}, None, None, []),
        # empty result
        ({'edx_username': ['test']}, 'username=test', '{"results":[]}', []),
        # return a mapped user
        ({'edx_username': ['test']}, 'username=test',
         '{"results":[{"username": "test", "remote_id": "test_rid"}]}',
         [{'edx_username': 'test', 'remote_id': 'test_rid'}]),
    )
    @unpack
    def test_load(self, load_params, url_params, response_body, expect_users, mock_request, mock_urlopen):
        mock_urlopen.return_value = StringIO(response_body)
        provider = EdxUsernameProvider()
        users = provider.load(**load_params)
        if load_params:
            mock_request.assert_called_once_with(
                'http://edx.org/api/user?{}'.format(url_params), None, {'Authorization': 'Bearer token'})
            mock_urlopen.assert_called_once_with(mock_request.return_value)
        self.assertListEqual(users, expect_users)

    @patch('idm.plugins.providers.urllib2.urlopen')
    @patch('idm.plugins.providers.urllib2.Request')
    def test_load_expection(self, mock_request, mock_urlopen):
        mock_urlopen.side_effect = urllib2.URLError('error')
        provider = EdxUsernameProvider()
        with self.assertRaises(RuntimeError):
            provider.load(edx_username='test')




