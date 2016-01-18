import logging
from collections import defaultdict
from itertools import chain

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from idm.plugins.manager import PluginManager
from idm.utils import select_providers, sort_by_dependencies, merge_dicts

logger = logging.getLogger(__name__)

unique_keys = ['user_id', 'edx_username', 'email', 'student_number', 'employee_number', 'remote_id']


def merge_users(*users):
    ret = chain(*users)

    for key in unique_keys:
        collector = defaultdict(dict)
        unmerged = []
        for user in ret:
            if key in user and user[key] is not None:
                collector[user[key]].update(user.iteritems())
            else:
                unmerged.append(user)
        ret = collector.values() + unmerged

    return ret


class SingleMappingView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """
        Identity mapping API
        ---
        # YAML
        type:
          name:
            required: true
            type: string
          url:
            required: false
            type: url
          created_at:
            required: true
            type: string
            format: date-time

        parameters:
            - name: wants
              description: attributes returned
              required: false
              type: string
              paramType: query
            - name: [attribute]
              description: the attribute to query against
              required: true
              type: string
              paramType: query
        responseMessages:
            - code: 200
              message: success
        """
        params = request.query_params
        users = []
        retrieved_fields = []
        key_names = PluginManager.get_all_needs()
        wants = params.getlist('wants', ['user_id'])
        for key_name in [key_name for key_name in key_names if key_name in params]:
            keys = params.getlist(key_name)
            users.extend([{key_name: key_value} for key_value in keys])
            retrieved_fields.append(key_name)
            providers = select_providers(PluginManager.get_all_providers(), wants, [key_name])
            providers = sort_by_dependencies(providers, [key_name])
            for provider in providers:
                load_by = provider.can_load(retrieved_fields)
                if load_by:
                    logger.info('Using {} with {}'.format(provider, retrieved_fields))
                    users = merge_users(
                        users, provider.load(**{load_by: [user[load_by] for user in users if load_by in user]}))
                    retrieved_fields.extend(provider.get_provides())

        # filter out unwanted attributes and use None for missing ones
        default_user_dict = {key: None for key in wants}
        users = [merge_dicts(default_user_dict, {key: value for key, value in user.iteritems() if key in wants})
                 for user in users]

        return Response(users)


class AttributeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        needs = set()
        provides = set()
        for provider in PluginManager.get_all_providers():
            needs.update(provider.get_needs())
            provides.update(provider.get_provides())

        return Response({'needs': needs, 'provides': provides})
