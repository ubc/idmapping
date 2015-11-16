import copy
from collections import OrderedDict

from django.utils import six


class AttributeLoadingDependencyNotSatisfied(RuntimeError):
    pass


def copy_provided_by(provided_by):
    new_provided_by = OrderedDict()
    for key in provided_by.keys():
        new_provided_by[key] = copy.copy(provided_by[key])

    return new_provided_by


def calculate_total_cost(providers):
    return sum([provider.get_cost() for provider in providers])


def is_in(value, elements):
    if isinstance(value, six.string_types):
        return value in elements
    else:
        return any([e in value for e in elements])


def remove(origin, elements):
    if isinstance(elements, six.string_types):
        elements = [elements]
    return [e for e in origin if not is_in(e, elements)]


def _select_providers(provided_by, wants, given):
    selected_providers = set()
    provided_by_clone = copy_provided_by(provided_by)
    wants_clone = remove(wants, given)
    given_clone = set(given)
    next_attr = None
    found = True
    while found:
        found = False
        # first find the attributes that can be provided by only one provider
        # we have to use those providers
        for attr, providers in provided_by_clone.copy().iteritems():
            if attr not in provided_by_clone or remove(wants_clone, attr) == wants_clone:
                # already found the provider to provide this attr or the attr is not what we are interested in
                continue
            if len(providers) != 1:
                next_attr = attr
                break
            if not set(providers[0].get_needs()) - {attr}:
                # can't use this provider as attr is the only attribute needed to query
                continue

            # select this provider because it is the only one providing this attr
            selected_providers.add(providers[0])
            # update wants for newly selected provider
            wants_clone = remove(wants_clone, providers[0].get_provides())
            if not providers[0].can_load(given_clone):
                wants_clone.append(providers[0].get_needs())
            else:
                # add attributes that selected provider can provides to the given set
                given_clone.update(set(providers[0].get_provides()) | {attr})
            remove(wants_clone, attr)
            if not wants_clone:
                # found everything, returning...
                return selected_providers
            # remove attr from the candidates
            del provided_by_clone[attr]
            # found a provider, so we start from beginning again
            found = True
            break

    if provided_by_clone and next_attr:
        # now we start from the attributes that have more than one providers, we start the search
        # we need to try all possible combinations to see which path gives the least providers
        best_path = None
        for provider in provided_by_clone[next_attr]:
            new_provided_by = copy_provided_by(provided_by_clone)
            new_provided_by[next_attr] = [provider]
            new_provided_by = OrderedDict(sorted(new_provided_by.items(), key=lambda t: len(t[1])))

            try:
                current_path = _select_providers(new_provided_by, wants_clone, frozenset(given_clone))
            except AttributeLoadingDependencyNotSatisfied:
                # this path doesn't work, next one
                continue
            if current_path and (not best_path or calculate_total_cost(best_path) > calculate_total_cost(current_path)):
                best_path = current_path
        # no path found that can satisfy all attributes we want
        if not best_path:
            raise AttributeLoadingDependencyNotSatisfied('Could not satisfy the loading dependencies for attributes.')
        # add the best result to selected_providers
        selected_providers.update(best_path)

    return selected_providers


def select_providers(providers, wants, given):
    """
    Select the providers that can provide the attributes in *wants* from the *providers* in lowest costs

    Args:
        providers (list[Plugin]): list of providers
        wants (list[str]): list of attributes that need to get from providers
        given (list[str]): list of the attributes that being provided already

    Returns:
        set[Plugin]: list of providers that need to provide required attributes
    """
    # a dict with provider list as value {'attr': [provider1, provider2], ...}
    provided_by = {}
    for provider in providers:
        for attr in provider.get_provides():
            provided_by.setdefault(attr, [])
            provided_by[attr].append(provider)

    # check if there is any attribute that doesn't have any provider to provide
    missing = set(wants).difference(provided_by.keys())
    if missing:
        raise RuntimeError(
            'Could not find providers that provides the following attributes: {}'.format(','.join(missing))
        )

    provided_by = OrderedDict(sorted(provided_by.items(), key=lambda t: len(t[1])))

    try:
        best_providers = _select_providers(provided_by, wants, frozenset(given))
    except AttributeLoadingDependencyNotSatisfied as e:
        e.message = e.message + ' Given attributes {}'.format(','.join(given))
        raise e

    return best_providers


def sort_by_dependencies(providers, given):
    given_clone = copy.copy(given)
    providers_clone = copy.copy(providers)
    sorted_providers = []
    while providers_clone:
        found = False
        for provider in providers_clone.copy():
            if provider.can_load(given_clone):
                sorted_providers.append(provider)
                providers_clone.remove(provider)
                given_clone.extend(provider.get_provides())
                found = True
        if not found:
            raise RuntimeError('Could not satisfy the loading dependencies')

    return sorted_providers


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
