import unittest

from mock import Mock

from idm.plugins.manager import PluginManager, BaseProvider
from idm.plugins.providers import EdxUsernameProvider, UserInfoProvider


class PluginManagerTest(unittest.TestCase):
    def testRegister(self):
        providers = PluginManager.get_all_providers()
        providers.sort(key=lambda p: p.name)
        for idx, providerClass in enumerate([EdxUsernameProvider, UserInfoProvider]):
            self.assertIsInstance(providers[idx], providerClass)

    def test_get_all_needs(self):
        needs = PluginManager.get_all_needs()
        self.assertItemsEqual(
            needs, ['user_id', 'employee_number', 'edx_username', 'remote_id', 'cwl', 'student_number', 'email'])

    def test_get_all_keys(self):
        keys = PluginManager.get_all_keys()
        self.assertItemsEqual(
            keys, ['user_id', 'employee_number', 'edx_username', 'remote_id', 'cwl', 'student_number', 'email'])


class BaseProviderTest(unittest.TestCase):
    def setUp(self):
        self.provider = BaseProvider()

    def test_get_cost(self):
        self.assertEqual(self.provider.get_cost(), 50)
        self.provider.cost = 40
        self.assertEqual(self.provider.get_cost(), 40)

    def test_get_needs(self):
        with self.assertRaises(NotImplementedError):
            self.provider.get_needs()

    def test_get_provides(self):
        with self.assertRaises(NotImplementedError):
            self.provider.get_provides()

    def test_get_keys(self):
        with self.assertRaises(NotImplementedError):
            self.provider.get_keys()

    def test_provides(self):
        self.provider.get_provides = Mock(return_value=['attr1'])
        self.assertTrue(self.provider.provides('attr1'))
        self.assertFalse(self.provider.provides('attr2'))

    def test_get(self):
        self.provider.get_attr1 = Mock(return_value=['attr1'])
        self.assertEqual(self.provider.get('attr1', 'key'), ['attr1'])
        self.provider.get_attr1.assert_called_once_with('key')
        with self.assertRaises(NotImplementedError):
            self.provider.get('attr2', 'key')

    def test_repr(self):
        self.provider.name = 'test provider'
        self.assertEqual(str(self.provider), 'test provider')

    def test_can_load(self):
        self.provider.get_needs = Mock(return_value=['attr1'])
        self.assertTrue(self.provider.can_load('attr1'))
        self.assertFalse(self.provider.can_load('attr2'))

        self.provider.get_needs = Mock(return_value=['attr1', ['attr2', 'attr3']])
        self.assertTrue(self.provider.can_load('attr1'))
        self.assertTrue(self.provider.can_load(['attr2', 'attr3']))
        self.assertTrue(self.provider.can_load(['attr1', 'attr3']))
        self.assertFalse(self.provider.can_load(['attr3']))

    def test_laod(self):
        self.provider.load_settings = Mock()
        self.provider.load()
        self.provider.load_settings.assert_called_once_with()
