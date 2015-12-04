from collections import defaultdict
from itertools import chain

from rest_framework.response import Response
from rest_framework.views import APIView

from idm.utils import select_providers, sort_by_dependencies, merge_dicts
from idmap.plugin import Plugin

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

    def get(self, request, format=None):
        params = request.query_params
        users = []
        retrieved_fields = []
        key_names = ['user_id', 'edx_username', 'email']
        wants = params.getlist('wants', ['user_id'])
        for key_name in key_names:
            if key_name not in params:
                continue
            keys = params.getlist(key_name)
            users.extend([{key_name: key_value} for key_value in keys])
            retrieved_fields.append(key_name)
            providers = select_providers(Plugin.get_all_providers(), wants, [key_name])
            providers = sort_by_dependencies(providers, [key_name])
            for provider in providers:
                load_by = provider.can_load(retrieved_fields)
                if load_by:
                    users = merge_users(
                        users, provider.load(**{load_by: [user[load_by] for user in users if load_by in user]}))
                    retrieved_fields.extend(provider.get_provides())

        # filter out unwanted attributes and use None for missing ones
        default_user_dict = {key: None for key in wants}
        users = [merge_dicts(default_user_dict, {key: value for key, value in user.iteritems() if key in wants})
                 for user in users]

        return Response(users)


class AttributeView(APIView):
    def get(self, request, format=None):
        needs = set()
        provides = set()
        for provider in Plugin.get_all_providers():
            needs.update(provider.get_needs())
            provides.update(provider.get_provides())

        return Response({'needs': needs, 'provides': provides})
