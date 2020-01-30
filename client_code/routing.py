import anvil
from collections import namedtuple
from ._logging import logger  

#to print route logging messages set routing.logger.debug = True above your main_router form


path = namedtuple('path', ['form','url_pattern','url_keys','title','properties'])

"""private globals"""
_paths = []  #List[path]
_error_form = None  #Form to load if a URL is not valid
_cache = {} #url_pattern: string, url_dict: dict, form: Form()
_current_form = None  # the current form that should be on the content panel - this is useful for slow form loads and quick navigation
_main_router = None  # this will be the main router - get_open_form() can break if the main_router hasn't loaded yet 
_on_navigation_stack_depth = 0

"""
Terminology and examples
             Example 1         |   Example 2
             __________________|_____________
url_hash:    'article?id=4'    |  'articles'
url_pattern: 'article'         |  'articles'   # default url_pattern is an empty string (i.e. the home page)
url_dict:    {'id': '3'}       |   {}          # if no parameters then url_dict is an empty dict
url_keys:    ['id']            |   []          # list[str]   the keys you expect from the url_dict - default is empty list
"""

"""
Form DECORATORS
@routing.main_router                                         ## above the MainForm that loads forms into it's content_panel. 
@routing.route(url_pattern=str, url_keys=[str], title=str)   ## defaults: url_pattern='', url_keys=[], title= #whatever is set in anvil's Titles and Logs
@routing.error_form                                          ## optional  - this form will load for an incorrect url or by calling router.load_error_form() 
"""
def main_router(Cls):
  """
  decorator for the main form
  @routing.main_router
  """
  class MainRouter(Cls):
    
    def __init__(self, **properties):
        global _main_router, _current_form
        _main_router = self
        
        Cls.__init__(self, **properties)
        # when this form is first loaded we 'navigate' based on the url
        self.on_navigation()  # called the first time the form is loaded to start routing...

        
    def on_navigation(self, url_hash=None, url_pattern=None, url_dict=None, path=None):
      # when there is navigation - back/forward navigation
      # or when the user changes the url_hash or when you call anvil.set_url_hash in code
      
      # calls the current_form's before_unload method
      # calls the MainForm's on_navigation method
      # get's the form to load (loads the error_form if there is no form to load)
      # loads the form

      global _on_navigation_stack_depth
      if _on_navigation_stack_depth > 5:
#         _on_navigation_stack_depth = 0
#         _on_navigation_stack_depth -= 1
        logger.print('**WARNING**  \nurl_hash redirected too many times without a form load, getting out\ntry setting redirect=False')
        return  # could change this to a raise
        # raise Exception('url_hash redirected too many times without a form load, try setting redirect=False')
      _on_navigation_stack_depth += 1

      if getattr(_current_form,'before_unload', None): 
        logger.print(f'{_current_form.__name__} before_unload called')
        """
        # before_unload in the form to be unloaded will be called here if the method exists
        # Mostly useful to prevent unloading the current form
        # it's not perfect so use with caution!!!
        # if you don't need to prevent a form from unloading ...but ...
        # ... do need to do something when the form is hidden use the form_hide event instead
        # To stop_unload return a value from the before_unload method
        """
        anvil.js.call_js('setUnloadPopStateBehaviour',True)
        stop_unload = _current_form.before_unload()    
        if stop_unload:
          logger.print(f"stop unload called from {_current_form.__name__}")
          anvil.js.call_js('stopUnload')
          _on_navigation_stack_depth -= 1
          return   #this will stop the navigation
        anvil.js.call_js('setUnloadPopStateBehaviour',False)
      
      if not (url_hash and url_pattern and url_dict):
        url_hash, url_pattern, url_dict = get_url_components()
      logger.print(f"on_navigation triggerd\nurl_hash    = {url_hash}\nurl_pattern = {url_pattern}\nurl_dict    = {url_dict}")
      
      if getattr(Cls,'on_navigation', None): 
        logger.print(f'{Cls.__name__} on_navigation called')
        # on_navigation in your main form will be called here
        # in the example we change 'selected' role on links using this method
        Cls.on_navigation(self, url_hash=url_hash, url_pattern=url_pattern, url_dict=url_dict, unload_form=_current_form)    

      try:
        if url_hash not in _cache and path is None:
          path = self.find_path(url_hash, url_pattern, url_dict)
      except KeyError:
        logger.print(f'no route form with url_pattern={url_pattern} and url_keys={url_dict.keys()}')
        if _error_form is not None:
          load_error_form()
        if anvil.get_open_form(): # raising an exception before there is an open form stops anything loading
          raise # if you can't work out why your page won't load then take raise out of this if block...
      except:
        raise  # this was an unexpected error so raise it
      else:
        self.content_panel.clear()  # clear the form now just incase we end up with a new to cache form that is slow to load later
        self.load_form(url_hash=url_hash, url_pattern=url_pattern, url_dict=url_dict, path=path)
      
      _on_navigation_stack_depth -= 1


    def find_path(self, url_hash, url_pattern, url_dict):
      # this method is called whenever we have form to load from navigation that is not in the cache 
      for path in _paths:
        if path.url_pattern == url_pattern and set(url_dict) == set(path.url_keys):
          return path
      else:
        #if no break we haven't found a valid hash so load the error form  
        raise KeyError(f'no route form with url_pattern={url_pattern} and url_keys={url_dict.keys()}')
    
    
    def load_form(self, url_hash, url_pattern, url_dict, path=None):
      global _current_form
      
      if url_hash in _cache:  
        logger.print(f"loaded {_cache[url_hash].__name__} from cache")
        _current_form = _cache[url_hash]
      elif path:
        title = path.title if path.title is None else path.title.format(**url_dict)
        _cache[url_hash] = path.form(url_hash=url_hash, url_pattern=url_pattern, url_dict=url_dict, 
                                        title=title,   from_routing=True,        **path.properties)
        logger.print(f"loaded {_cache[url_hash].__name__}, added to cache")
      else:
        raise Exception('bad load_form called')
      if _current_form is _cache[url_hash]: # this accounts for a slow form load and a super quick navigation change!
        form = _cache[url_hash]
        url_hash, url_pattern, url_dict = get_url_components() #just incase they changed!
        form.url_hash    = url_hash
        form.url_pattern = url_pattern
        form.url_dict    = url_dict
        
        anvil.js.call_js('setTitle', form._route_title)
        self.content_panel.clear()
        self.content_panel.add_component(form)
          
  return MainRouter


class route():
  """ 
  the route decorator above any form you want to load in the content_panel
  @routing.route(url_pattern=str,url_keys=List[str], title=str)
  """
  def __init__(self, url_pattern ='', url_keys=[], title=None):
    self.url_pattern = url_pattern
    self.url_keys    = url_keys
    self.title       = title
  def __call__(self, Cls):
    if not isinstance(self.url_pattern, str):
      raise TypeError(f'url_pattern must be type str not {type(self.url_pattern).__name__} in {Cls.__name__}')
    if not (isinstance(self.url_keys, list) or isinstance(self.url_keys, list)):
      raise TypeError(f'keys should be a list or tuple not {type(self.url_keys).__name__} in {Cls.__name__}')
    if not (self.title is None or isinstance(self.title, str)):
      raise TypeError(f'title must be type str or None not {type(self.title).__name__} in {Cls.__name__}')
    
    class Route(Cls):
      def __init__(self, url_hash=None, url_pattern=None, url_dict=None, title=None, 
                   route=True, from_routing=False, **properties):
        if route:
          if not from_routing:
            raise Exception(f'{self.__name__} is a route form and was not loaded from routing - check the docs - or set route=False to ignore routing behaviour')
          global _current_form
          _current_form = self #this is the form that should be displayed can cause some issues if this form takes a while to load          

          self.url_hash     = url_hash
          self.url_pattern  = url_pattern
          self.url_dict     = url_dict
          self._route_title = title
          self.route        = route
          self.from_routing = from_routing
         
        if 'anvil' in str(Cls.__bases__):  # then this was the original class Form(FormTemplate) Class
          Cls.__init__(self, **properties)  # prevents console logging 'Ignoring form constructor kwarg:' which is annoying
        else: # we have a multple decorator so re-pass route kwargs
          Cls.__init__(self, url_hash=url_hash,  url_pattern=url_pattern, url_dict=url_dict, title=title, 
                                route=route, from_routing=from_routing, **properties)
    
    Route.__name__ = Cls.__name__  #prevents the form being called Route
    _paths.append(path(Route, self.url_pattern, self.url_keys, self.title, {}))
    
    return Route

  
def error_form(Cls):
  """ optional decorator - this is the error form simply use the decorator above your error Form
  @routing.error_form
  """
  class ErrorForm(Cls):
    def __init__(self, **properties):
      Cls.__init__(self, **properties)
      self._route_title=None # route form needs this to load from cache...
  global _error_form
  _error_form = ErrorForm
  return ErrorForm


"""
METHODS 

routing.get_url_components()                          returns url_hash, url_pattern, url_dict
routing.get_url_hash()                                returns url_hash as a string (different to anvil.get_url_hash() which could be a dict)
routing.get_url_pattern()                             returns url_pattern 
routing.get_url_dict()                                returns url_dict 

routing.remove_from_cache(url_hash)
routing.add_to_cache(url_hash, form)                  nb: the form should be initiated already like ArticleForm()
routing.clear_cache()

routing.set_url_hash(url_hash, **kwargs)              augments anvil's usual set_url_hash() method see doc_string for **kwargs
routing.load_form(form, **properties)                 routing loads the form with the properties you pass
                                                      see the docstring for additional **kwargs
                                                      nb: if it is in the cache then it will load from cache (load_from_cache=False is possible)
                                                      nb: the form should NOT be initiated e.g. load_form(ArticleForm)
routing.load_error_form()                             loads the error form and adds it to the cache at the current url
"""

def get_url_components(url_hash=None):
  """returns  url_hash, url_pattern, url_dict
  this will get the components from the current addressbar url_hash unless you provide a url_hash to decode
  """
  if url_hash is None:
    #url_hash = anvil.get_url_hash()  #changed since anvil decodes the url_hash
    url_hash  = anvil.js.call_js('getUrlHash')
  if isinstance(url_hash,dict):
    # this is the case when anvil converts the url hash to a dict automatically
    url_pattern = ''
    url_dict    = {k:(anvil.http.url_decode(v) if v != 'undefined' else '') for k,v in url_hash.items()} #anvil.get_url_hash return 'undefined' for empty parameters
    url_hash    = '?' + '&'.join(f'{key}={anvil.http.url_encode(value)}' for key,value in url_dict.items())
  elif url_hash.find('?')==-1: # then we have no parameters as part of the url 
    url_pattern = url_hash
    url_dict    = {}
  else:
    url_pattern, url_dict = url_hash.split('?',1)  
    key_value_pairs = url_dict.split('&')
    for i, pair in enumerate(key_value_pairs):
      if '=' not in pair:
        key_value_pairs[i] = pair + '='
      key, value = pair.split('=',1)  
      key_value_pairs[i]   = f"{key}={anvil.http.url_decode(value)}"      
    url_dict = dict(pair.split('=', 1) for pair in key_value_pairs)

  return url_hash, url_pattern, url_dict

def get_url_hash(url_hash=None):
  return get_url_components(url_hash=url_hash)[0]

def get_url_pattern(url_hash=None):
  return get_url_components(url_hash=url_hash)[1]

def get_url_dict(url_hash=None):
  return get_url_components(url_hash=url_hash)[2]


def remove_from_cache(url_hash=None, *, url_pattern=None, url_dict=None):
  """useful if you don't want a form to load from the cache or say the hash represents a page that gets deleted
  gotcha: cannot be called from the init function of the the same form in cache
  because the form has not been added to the cache until it has loaded - try putthing it in the form show even instead
  """
  url_hash = _process_url_arguments(url_hash, url_pattern=url_pattern, url_dict=url_dict)[0]
  logger.print(f'removing {url_hash} from cache')
  if url_hash in _cache:
    del _cache[url_hash]
  else:
    logger.print(f"*warning* {url_hash} was not found in cache - maybe the form was yet to load")



def add_to_cache(url_hash, form):
  """the form should be initiated 
  useful if you have a form instance and want to add it to cache without navigating to it
  """
  logger.print(f'adding {url_hash} to cache with {form.__name__}')
  _cache[url_hash] = form


def clear_cache():
  """clears the _cache"""
  logger.print(f"clearing the cache")
  global _cache
  _cache = {}
  

def set_url_hash(url_hash=None, *, #the remaining are keyword only arguments
                 url_pattern=None, url_dict=None,
                 
                 replace_current_url=False, 
                 set_in_history     =True,
                 redirect           =True, 
                 load_from_cache    =True
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
                      
  redirect            = True -  this will set the main_routers on_navigation method to fire - 
                      = False -  on_navigation won't be fired
  load_from_cache     = True - on_navigation will load from _cache if the url_hash exists in _cache
                      = False - the url_hash is removed from _cache
  """
  if not set_in_history and not replace_current_url:
    raise Exception('cannot do set_in_history=False and replace_current_url=False\nPushing new url without adding to history stack is impossible')
  
  ### process the url_arguments
  url_hash, url_pattern, url_dict = _process_url_arguments(url_hash, url_pattern=url_pattern, url_dict=url_dict)
  if url_hash == get_url_hash():
    return  #should not continue if url_hash is identical to the addressbar hash!

  # remove from cache  
  if not load_from_cache:
    remove_from_cache(url_hash)

  
  if       set_in_history and not replace_current_url:
    logger.print(f"setting url_hash to: #{url_hash}, adding to top of history stack")
    anvil.js.call_js('pushState', '#'+url_hash)
  elif     set_in_history and    replace_current_url:
    logger.print(f"setting url_hash to: #{url_hash}, replacing current_url, setting in history")
    anvil.js.call_js('replaceState', '#'+url_hash)
  elif not set_in_history and     replace_current_url:
    logger.print(f"setting url_hash to: #{url_hash}, replacing current_url, NOT setting in history")
    anvil.js.call_js('replaceUrlNotState', '#'+url_hash)
  
  if redirect:
    _main_router.on_navigation(url_hash, url_pattern, url_dict)
  elif set_in_history:
    _cache[url_hash] = _current_form    #no need to add to cache if not being set in history
  
    
def load_form(form, url_pattern=None, url_keys=[], *, replace_current_url=False, set_in_history=True, load_from_cache=True, **properties):
  """loads the form with properties - in most instances better to just do routing.set_url_hash
  useful if you want to pass an item to a form say... or don't like to use routing.set_url_hash
  
  note the expected url_hash is already in cache then the cached form will load unless you set load_from_cache = False
  
  if you are using a url_dict for this route form then you must pass a kwarg that has the correct keys somewhere in the **properites
  e.g.  ArticleForm as the route decorator @routing.route('article', ['id'])
  'id' is a required key so load_form can be called in. the following ways:
  load_form(ArticleForm, item=item)          #  where 'id' is a key in item...
  load_form(AritcleForm, id=3, item=item)    #  as above but this is quicker if item is a live_object_proxy as it prevents a server call
  """
  try:
    path = _get_path(form, url_pattern, url_keys)
  except:
    raise

  url_pattern = path.url_pattern
  url_dict    = _get_url_dict(path.url_keys, form, **properties)
  url_hash    = _get_url_hash(url_pattern, url_dict)
  
  if not replace_current_url and not set_in_history:
    raise Exception('cannot do set_in_history=False and replace_current_url=False')

  if url_hash == get_url_hash():
    return  #should not continue if url_hash is identical to the addressbar hash!

  if replace_current_url and set_in_history:
    logger.print(f"loading form {form.__name__}, with url_hash: #{url_hash}, replacing current url, setting in history")
    anvil.js.call_js('replaceState','#' + url_hash)
  elif replace_current_url:
    logger.print(f"loading form {form.__name__}, with url_hash: #{url_hash}, replacing current url, NOT setting in history")
    anvil.js.call_js('replaceUrlNotState', '#' + url_hash)
  else:
    logger.print(f"loading form {form.__name__}, with url_hash: #{url_hash}, adding to top of history stack")
    anvil.js.call_js('pushState', '#' + url_hash)
    
  if not load_from_cache:
    remove_from_cache(url_hash)

  
  path.properties.update(**properties)  # load the properties to path
  _main_router.on_navigation(url_hash=url_hash, url_pattern=url_pattern, url_dict=url_dict, path=path)
  for key in path.properties:  # set the properties back to an empty dict
    del path.properties[key]
  

def load_error_form():
  """loads the error form - note that the url_hash is not changed
  could make this #404 if desired by adding anvil.js.call_js('replaceState',"#404")
  """
  logger.print("loading error form")
  url_hash, _, _ = get_url_components()
  _cache[url_hash] = _error_form()
  global _current_form
  _current_form = _cache[url_hash]
  _main_router.content_panel.clear()
  _main_router.content_panel.add_component(_cache[url_hash])


"""Helper functions for load_form"""
def _get_url_dict(url_keys, form, **properties):
  url_dict = properties.get('url_dict')  # just in case the user decided to pass the url_dict as a kwarg...
  if url_dict is None:  #if a url dict is expected then either a url_dict shoud have been provided - or the url_keys should have been passed as kwargs
    url_dict = {key:_finditem(properties, key) for key in url_keys}
    for key,value in url_dict.items():
      if value == "NOT FOUND":
        raise KeyError(f'{form.__name__} expected the key {key} to be passed to method form_load()')
  return url_dict
  

def _get_url_hash(url_pattern, url_dict):
  url_params  = '&'.join(f'{key}={anvil.http.url_encode(str(value))}'for key, value in url_dict.items())
  url_params  = '?' + url_params if url_params else ''
  return url_pattern + url_params


def _finditem(obj, key):
  # this function is called when a route form expects a key which will be passed as an attribute by a form
  # typically this might be a key within the item object but could be anywhere within the properties passed to the form
  if key in obj: 
    return obj[key]
  for k, v in obj.items():
    if isinstance(v,dict) or isinstance(v, LiveObjectProxy):
      item = _finditem(v, key)
      if item is not None:
        return item
  return "NOT FOUND"  #used as a way to check if this method failed to find an item

  
def _get_path(form, url_pattern, url_keys):
  paths_with_form = [path for path in _paths if path.form.__name__ == form.__name__]
  num_paths       = len(paths_with_form)
  if not num_paths:
    raise Exception(f'{form.__name__} is not a route form - use the route decorator')
  elif num_paths == 1:
    return paths_with_form[0]
  elif url_pattern is None:
       raise KeyError(f'{form.__name__} has multiple decorators - you must provide a url_pattern [and url_keys] with load_form()')
  else:
    for path in paths_with_form:
      if path.url_pattern == url_pattern and set(url_keys) == set(path.url_keys): 
        return path
    raise KeyError(f'{form.__name__} has no decorator with url_pattern={url_pattern} and url_keys={url_keys}')


def _process_url_arguments(url_hash=None, *, url_pattern=None, url_dict=None):
  """ 
  check and set_up the url_hash, url_pattern and url_dict
  """
  if url_dict is not None and url_pattern is None:
    raise TypeError('if you provide a url_dict you must provide a url_pattern as a keyword argument url_pattern=')
  if url_hash is None and url_pattern is None:
    url_hash = '' #default behaviour should be an empty string
  elif url_hash is None:
    url_dict = {} if url_dict is None else url_dict
    url_hash = _get_url_hash(url_pattern, url_dict)
  url_hash, url_pattern, url_dict = get_url_components(url_hash)  # will convert to a string
  return url_hash, url_pattern, url_dict

    
def set_warning_before_app_unload(warning=True):
  if not isinstance(warning, bool):
    raise TypeError(f"warning={warning} must be a boolean")
  anvil.js.call_js('setAppUnloadBehaviour', warning)

def replace_current_url(url_hash, *args, redirect=False, set_in_history=True, **kwargs):
  raise AttributeError(f'replace_current_url depriciated, use: \nrouting.set_url_hash({url_hash}, \nreplace_current_url=True, \nredirect={redirect}, \nset_in_history={set_in_history})')

