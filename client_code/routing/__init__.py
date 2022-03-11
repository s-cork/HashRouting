# SPDX-License-Identifier: MIT
#
# Copyright (c) 2021 The Anvil Extras project team members listed at
# https://github.com/anvilistas/anvil-extras/graphs/contributors
#
# This software is published at https://github.com/anvilistas/anvil-extras

__version__ = "1.9.0"

from anvil.js import window as _w

from . import _navigation
from . import _router as _r
from ._decorators import error_form, route, template
from ._logging import log as _log
from ._logging import logger
from ._router import NavigationExit, launch
from ._utils import (
    _process_url_arguments,
    get_url_components,
    get_url_dict,
    get_url_hash,
    get_url_pattern,
)

logger.debug = False

default_template = template()
main_router = default_template  # backwards compatability


#### some helpers #####
def reload_page(hard=False):
    """reload the current page"""
    if hard:
        _log(lambda: "hard reload_page called")
        _w.location.reload()
    else:
        _log(
            lambda: "reload_page called, clearing the cache for this page and reloading"
        )
        url_hash, url_pattern, url_dict = get_url_components()
        remove_from_cache(url_hash)
        _r.navigate(url_hash, url_pattern, url_dict)


def go_back():
    """go to previous page"""
    _log(lambda: "going back a page")
    _w.history.back()


def go(x=0):
    """go forward x pages (use negative x to go back)"""
    if not isinstance(x, int):
        raise TypeError(f"go requires an int not {type(x)}")
    _log(lambda: f"go called with with x={x}")
    _w.history.go(x)


def on_session_expired(reload_hash=True, allow_cancel=True):
    """override anvil's default session expired behaviour"""
    print(
        "Deprecated: it is now possible to catch a SessionExpiredError in the anvil.set_default_error_handler() callback"
    )
    if type(reload_hash) is not bool:
        raise TypeError(f"reload_hash must be a bool not {type(reload_hash)}")
    if type(allow_cancel) is not bool:
        raise TypeError(f"allow_cancel must be a bool not {type(allow_cancel)}")
    from ._session_expired import session_expired_handler

    session_expired_handler(reload_hash, allow_cancel)


def set_warning_before_app_unload(warning=True):
    """set a warning message before someone tries to navigate away from the app"""
    _log(lambda: f"Setting warning before app unload set to: {warning}")

    def beforeunload(e):
        e.preventDefault()  # cancel the event
        e.returnValue = ""  # chrome requires a returnValue to be set

    _w.onbeforeunload = beforeunload if warning else None


def remove_from_cache(url_hash=None, *, url_pattern=None, url_dict=None):
    """useful if you don't want a form to load from the cache or say the hash represents a page that gets deleted
    gotcha: cannot be called from the init function of the the same form in cache
    because the form has not been added to the cache until it has loaded - try putthing it in the form show even instead
    """
    url_hash = _process_url_arguments(
        url_hash, url_pattern=url_pattern, url_dict=url_dict
    )[0]
    _log(lambda: f"removing {url_hash!r} from cache")
    cached = _r._cache.pop(url_hash, None)
    if cached is None:
        _log(
            lambda: f"*warning* {url_hash!r} was not found in cache - maybe the form was yet to load"
        )


def get_cache():
    return _r._cache


def add_to_cache(url_hash, form):
    """the form should be initiated
    useful if you have a form instance and want to add it to cache without navigating to it
    """
    _log(lambda: f"adding {url_hash!r} to cache with {form.__class__.__name__!r}")
    _r._cache[url_hash] = form


def clear_cache():
    _log(lambda: "clearing the cache")
    _r._cache.clear()


def load_error_form():
    return _r.load_error_form()


def set_url_hash(
    url_hash=None,
    *,  # the remaining are keyword only arguments
    url_pattern=None,
    url_dict=None,
    replace_current_url=False,
    set_in_history=True,
    redirect=True,
    load_from_cache=True,
    **properties,
):
    """either provide a url_hash or a url_pattern or a url_pattern and url_dict
    note: url_hash can be a dictionary: set_url_hash({'key':value}) is valid and would set the url_hash="#?key=value"

    default behaviour will be as anvil.set_url_hash
    if no arguments are provided then url_hash will be an empty string.

    replace_current_url = False - pushes a new url to the history stack (the default behaviour)
                          nb: it is impossoble to push a new url to the history stack and have set_in_history=False
                        = True - repaces the current url in the address bar
    set_in_history      = True - the new url is added to the history stack so appears in back/foward navigation
                        = False - the current url remains in the history stack and will appear on back/forward navigation

    redirect            = True -  this will set the main_routers  navigate method to fire -
                        = False -   navigate won't be fired
    load_from_cache     = True -  navigate will load from _cache if the url_hash exists in _cache
                        = False - the url_hash is removed from _cache

    properties          any additional kwargs will be passed to the form
    """
    if not set_in_history and not replace_current_url:
        raise Exception(
            "cannot do set_in_history=False and replace_current_url=False\nPushing new url without adding to history stack is impossible"
        )

    ### process the url_arguments
    url_hash, url_pattern, url_dict = _process_url_arguments(
        url_hash, url_pattern=url_pattern, url_dict=url_dict
    )

    # remove from cache
    if not load_from_cache:
        remove_from_cache(url_hash)

    if (
        url_hash == get_url_hash()
        and url_hash in _r._cache
        and _r._current_form is not None
    ):
        return  # should not continue if url_hash is identical to the addressbar hash!
        # but do continue if the url_hash is not in the cache i.e it was manually removed

    if set_in_history and not replace_current_url:
        _log(
            lambda: f"setting url_hash to: '#{url_hash}', adding to top of history stack"
        )
        _navigation.pushState(url_hash)
    elif set_in_history and replace_current_url:
        _log(
            lambda: f"setting url_hash to: '#{url_hash}', replacing current_url, setting in history"
        )
        _navigation.replaceState(url_hash)
    elif not set_in_history and replace_current_url:
        _log(
            lambda: f"setting url_hash to: '#{url_hash}', replacing current_url, NOT setting in history"
        )
        _navigation.replaceUrlNotState(url_hash)

    if redirect:
        _r.navigate(url_hash, url_pattern, url_dict, **properties)
    elif set_in_history and _r._current_form:
        _r._cache[
            url_hash
        ] = _r._current_form  # no need to add to cache if not being set in history


def load_form(*args, **kws):
    raise RuntimeError("load_form is deprecated")
