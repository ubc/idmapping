from django.utils import six
from django.utils.module_loading import import_string


class Plugin(object):
    """
    Plugin base class
    """
    name = 'Default Plugin'
    cost = 50

    # class __metaclass__(type):
    #
    #     def __init__(cls, name, base, attrs, what):
    #         if not hasattr(cls, 'registered'):
    #             cls.registered = []
    #         else:
    #             cls.registered.append(cls)

    @classmethod
    def register(cls, *plugin_paths):
        plugin_paths = list(plugin_paths)
        #for _, name, _ in pkgutil.iter_modules(paths):
        for plugin_path in plugin_paths:
            plugin_class = import_string(plugin_path)
            if not hasattr(cls, 'registered'):
                cls.registered = []
            cls.registered.append(plugin_class())

            # fid, pathname, desc = imp.find_module(name, paths)
            # try:
            #     imp.load_module(name, fid, pathname, desc)
            # except Exception as e:
            #     logging.warning("could not load plugin module '%s': %s", pathname, e.message)
            # if fid:
            #     fid.close()

    @classmethod
    def find_provider(cls, field):
        for plugin in cls.registered:
            if plugin.provides(field):
                return plugin

        return None

    @classmethod
    def get_all_providers(cls):
        return cls.registered

    def get_cost(self):
        return self.cost

    def get_needs(self):
        raise NotImplementedError

    def get_provides(self):
        raise NotImplementedError

    def provides(self, field):
        return field in self.get_provides()

    def get(self, field, key):
        func_name = 'get_{}'.format(field)
        if not hasattr(self, func_name):
            raise NotImplementedError('Getter method get_{} from {} is not implemented!'.format(field, self.name))

        return getattr(self, func_name)(key)

    def can_load(self, given):
        needs = self.get_needs()
        for need in needs:
            if isinstance(need, six.string_types):
                if need in given:
                    return need
            else:
                # list of requirements has to be satisfied all
                if all([x in given for x in need]):
                    return need

        return None

    def __repr__(self):
        return self.name
