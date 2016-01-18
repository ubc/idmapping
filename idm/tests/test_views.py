from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from idm.views import SingleMappingView


class SingleMappingViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test', password='test')

    def test_map_without_parameters(self):
        request = self.factory.get('/map')
        request.user = self.user

        response = SingleMappingView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.data, [])
