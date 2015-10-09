import hashlib
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


def hash_md5(local_id, salt):
    return hashlib.md5(local_id + salt).hexdigest()


class SingleMappingView(APIView):

    def get(self, request, format=None):
        params = request.query_params
        user_id = ''
        remote_id = ''
        if 'user_id' in params:
            user_id = params['user_id']
            remote_id = hash_md5(user_id, settings.HASH_SALT)

        return Response({'user_id': user_id, 'remote_id': remote_id})

