# HashRouting
HashRouting - a dependency for anvil.works that allows navigation in apps


| | |
|---|---|
| Dependency Clone Link:| [<img src="https://anvil.works/img/forum/copy-app.png" height='40px'>](https://anvil.works/build#clone:ZKNOF5FRVLPVF4BI=JHFO3AIV2GTM5ZP4FPFL3SMI)|
|Live Example: |[hash-routing-example.anvil.app](https://hash-routing-example.anvil.app/) |
|Example Clone Link with dependency: | [<img src="https://anvil.works/img/forum/copy-app.png" height='40px'>](https://anvil.works/build#clone:JVKXENWGKTU6IO7Y=O62PB7QCYEEU4ZBDTJQ6V6W4%7cZKNOF5FRVLPVF4BI=JHFO3AIV2GTM5ZP4FPFL3SMI)|


---
## Introduction

An Anvil app is a Single Page App so when the user navigates through the app pages the URL does not change. The part of the URL before the `#` is used by the server to identify the app, while the part following the `#`, known as hash, is never sent to the server, is used only by the browser. 

The routing module uses the hash to define unique URLs for each form, page or whatever your app is showing. Here are a few examples of URLs pointing to different forms of the same app, or displaying different data on the same form:

URL|Description |`url_hash`|`url_pattern`|`url_dict`|`url_keys`
---|---|---|---|---|---
`blog.anvil.app/#`|Show the app home page|`''`|`''`|`{}`|`[]`
`blog.anvil.app/#blogposts`|Show the list of blogs posts|`'blogposts'`|`'blogposts'`|`{}`|`[]`
`blog.anvil.app/#tags`|Show the list of tags|`'tags'`|`'tags'`|`{}`|`[]`
`blog.anvil.app/#blogpost?id=10`|Show the blog post by ID|`'blogpost?id=10'`|`'blogpost'`|`{'id':'10'}`|`['id']`


---

## Main Form

This is the startup form, the one loaded when the app starts. It contains the header, the navigation bar and a `content_panel` where all the other forms will be loaded during the life of the app.

The `MainForm` is **not** the `HomeForm`. The `MainForm` has no content, only has navigation, header and infrastructure to show all the other forms.

- Import the routing module, all the forms used by the app
- and add the decorator: `@routing.main_router`

```python
from HashRouting import routing
from .Form1 import Form1
from .Form2 import Form2
from .Form3 import Form3
from .ErrorForm import ErrorForm

@routing.main_router
class Main(MainTemplate):
```
---

## All Route Forms

These are all the forms that are loaded inside the `MainForm`'s `content_panel`.

- Import the routing module and add the decorator that defines the page name (`url_pattern`) and the query string parameters (`url_keys`). This shows how to link a form to the URL `<appdomain.com>#article?id=123`:
```python
from HashRouting import routing

@routing.route('article', url_keys=['id'])
class ArticleForm(ArticleFormTemplate):
```

Or without any `url_keys`

```python
from HashRouting import routing

@routing.route('article')
class ArticleForm(ArticleFormTemplate):
```


## Home form

The `HomeForm` is also a `Route Form` that appears in the `content_panel` of the `MainForm`.

- Import the routing module and add the `route` decorator with the page name set to an empty string
```python
from HashRouting import routing

@routing.route('')
class Home(HomeTemplate):
```

---

## Error form (Optional)

This is the form that is shown when the `url_hash` refers to a page that does not exist or the query string does not match the `url_keys` listed in the decorator. 
Follow these steps to create an error form that shows an error message:

- Create a form with a label `Sorry, this page does not exist`
- Import the routing module and add the decorator `@routing.error_form`:
```python
from HashRouting import routing

@routing.error_form
class ErrorForm(ErrorFormTemplate):
```

---

## Navigation

It is important to never use the typical method to navigate when implementing `HashRouting`
```python
# Banned
get_open_form().content_panel.clear()
get_open_form().content_panel.add_component(Form1())
# This will result in an Exception('Form1 is a route form and was not loaded from routing')
```

Instead

```python
# option 1
set_url_hash('home') # anvil's built in method

# option 2
routing.set_url_hash('home') #routing's set_url_method has some bonus features... 

# option 3
routing.load_form(Home)
```

With parameters:

```python
# option 1
set_url_hash(f'article?id={self.item['id']}')

# option 2
routing.set_url_hash(f'article?id={self.item['id']}')

# option 3
routing.set_url_hash(url_pattern='article', url_dict={'id':self.item['id']})

# option 4
routing.load_form(ArticleForm, id=3)
```

`routing.set_url_hash` and `routing.load_form`  - have some additional kwargs that can be passed - some examples below.

<br>

<br>

# Notes and Examples

The following represents some notes and examples that might be helpful

<br>

## Form Arguments

`Form` `__init__` methods cannot have required named arguments. Something like this is not allowed:
```python
@routing.route('form1', url_keys=['key1'])
class Form1(Form1Template):
  def __init__(self, key1, **properties):
```
All the parameters listed in `url_keys` are required, and the rule is enforced by the routing module. If the `Route Form` has required `url_keys` then the routing module will provide a `url_dict` with the parameters from the `url_hash`.

This is the correct way:
```python
@routing.route('form1', url_keys=['key1'])
class Form1(Form1Template):
  def __init__(self, **properties):
    key1 = self.url_dict['key1']  #routing provides self.url_dict
```

---

## Security

**Security issue**: You log in, open a form with some data, go to the next form, log out, go back 3 steps and you see the cached stuff that was there when you were logged in.

**Solution 1**: When a form shows sensitive data it should always check for user permission in the `form_show` event, which is triggered when a cached form is shown.

**Solution 2**: Call `routing.clear_cache()` to remove the cache upon logging out.

---

## Multiple Route Decorators

It is possible to define optional parameters by adding multiple decorators, e.g. one with and one without the key. Here is an example that allows to use the `home page` with the default empty string and with one optional `search` parameter:
```python
@routing.route('')
@routing.route('', url_keys=['search'])
class Form1(Form1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.search_terms.text = self.url_dict.get('search', '')
```

Perhaps your form displays a different `item` depending on the `url_pattern`/`url_hash`:

```python
@routing.route('articles')
@routing.route('blogposts')
class ListItems(ListItemsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.item = anvil.server.call(f'get_{self.url_pattern}')  # self.url_pattern is provided by the routing module
```

---

## Navigation Techniques

### `redirect=False`

It is possible to set a new url without navigating away from the current form. For example a form could have this code:
```python
def search_click(self, **event_args):
  if self.search_terms.text:
    routing.set_url_hash(f'?search={self.search_terms.text}', 
                          redirect=False
                          )
  else:
    routing.set_url_hash('',
                          redirect=False,
                          )
  self.search(self.search_terms.text)
```
This way search parameters are added to the history stack so that the user can navigate back and forward but routing does not attempt to navigate to a new form instance. 

**IMPORTANT**

If you do `routing.set_url_hash` inside the `__init__` method or `form_show` event, be careful, you may cause an infinite loop if your `url_hash` points to the same form and `redirect=True`! 
<br>
In this case, you will get a `warning` from the `routing.logger` and navigation/redirection will be halted.

Navigation will be halted:
* after 5 navigation attempts without loading a form to `content_panel`

<br>

### `replace_current_url=True`
It is also possible to replace the current url in the history stack rather than creating a new entry in the history stack.

In the `ArticleForm` example perhaps we want to create a new article if the `id` parameter is empty like: `url_hash = "article?id="`

```python
@routing.route('article', url_keys=['id'])
class ArticleForm(ArticleFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run when the form opens.
    if url_dict['id']:
      self.item = anvil.server.call("get_article_by_id",self.url_dict['id'])
    else:
      # url_dict['id'] is empty
      self.item = anvil.server.call('create_new_article')
      routing.set_url_hash(f"article?id={self.item['id']",
                            replace_current_url=True,
                            set_in_history=True,
                            redirect=False
                          )
      

```


in the `routing.set_url_hash` method, default kwargs are as follows:
```python
"""
replace_current_url = False # Set to True if you want the url change to happen 'in place' rather than as a new history item
set_in_history      = True  # Set to False if you don't want the new Url in the browser history
redirect            = True  # Set to False if you don't wish to navigate away from current Form
load_from_cache     = True  # Set to False if you want the new URL to NOT load from cache
"""
```


- `routing.load_form` optional `kwargs` are the same, except for `redirect` which is not available.
- don't worry about calling `set_url_hash` to the current hash in the window address bar - nothing will happen. 

---


## Page Titles

You can set each `Route Form` to have a `title` parameter which will change the page title  

If you do not provide a title then the page title will be the default title provided by Anvil in your titles and logs

**Examples**:

```python
@routing.route('home', title='Home | RoutingExample')
@routing.route('',     title='Home | RoutingExample')
class Home(HomeTemplate):
```

```python
@routing.route('article', url_keys=['id'], title="Article-{id} | RoutingExample")
class ArticleForm(ArticleFormTemplate):
```

- Think `f strings` without the f
- Anything in curly braces should be an item from `url_keys`

---


## Full Width Rows

You can set a `Route Form` to load as a `full_width_row` by setting the `full_width_row` parameter to `True`.  

```python
@routing.route('home', title='Home', full_width_row=True)
class Home(HomeTemplate):
```

___
## Selected Links

To use the Material Design role `'selected'` for navigation you can add an `on_navigation` method to your `MainForm`

```python
@routing.main_router
class MainForm(MainFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run when the form opens.
    
    self.links = [self.articles_link, self.blog_posts_link]
    self.blog_posts_link.tag.url_hash = 'blog-posts'
    self.articles_link.tag.url_hash   = 'articles'


  def on_navigation(self, **nav_args):
    # this method is called whenever routing provides navigation behaviour
    # url_hash, url_pattern, url_dict are provided by the main_router class decorator
    for link in self.links:
      if link.tag.url_hash == nav_args.get('url_hash'):
        link.role = 'selected'
      else:
        link.role = 'default'
```

**Nav Args provided by the `main_router` class decorator**

```python
nav_args = {'url_hash':    url_hash, 
            'url_pattern': url_pattern, 
            'url_dict':    url_dict, 
            'unload_form': form_that_was_unloaded #could be None if initial call
            }
```

___

## Preventing a Form from Unloading (when navigating within the app)

Create a method in a `Route Form` called `before_unload` 

To prevent Unloading return a value

```python
def before_unload(self):
  # this method is called when the form is about to be unloaded from the content_panel
  if confirm('are you sure you want to close this form?'):
    pass
  else: 
    return 'STOP'
```

*NB*:
- Only use if you need to prevent unloading.
- Otherwise, the `form_hide` event should work just fine.

*NB*: 
- This method does not prevent a user from navigating away from the app entirely. 
(see the section **Leaving the App** below)

___

## Passing properties to a form

You can pass properties to a form by adding them as keyword arguments with either `routing.load_form` or `routing.set_url_hash` 

```python

def article_link_click(self, **event_args):
  routing.load_form(Article, id=self.item['id'], item=self.item)
  # if your RouteForm has required keys then you should provide these as kwargs 
  # nb the key id could also be a key in self.item in which case
  # routing.load_form(Article, item=self.item) is sufficient (but may be slower to load if item is a LiveObjectProxy [Table Row])

def article_link_click(self, **event_args):
  routing.set_url_hash(f'article?id={self.item["id"]'}, item=self.item)
```

---

## Sometimes my Route Form is a Route Form sometimes it is a Component

No problem... use the parameter `route=False` to avoid typical routing behaviour

```python
def button_click(self,**event_args):
  alert(ArticleForm(route=False))  
  #setting route = False stops the Route Form using the routing module...

```

---

## My `url_dict` contains the & symbol 

let's say your `url_dict` is `{'name': 'A & B'}` doing the following will cause a problem

```python
routing.set_url_hash('customer?name=A&B')
```

instead do

```python
routing.set_url_hash(url_pattern='customer', url_dict={'name':'A&B'})
```

HashRouting will encode this correctly

---

## I have a login form how do I work that?

### As part of `HashRouting` navigation
```python
@routing.main_router
class MainForm(MainFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    user = anvil.users.get_user()
    if user is None:
      routing.set_url_hash('login',
                           replace_current_url=True,
                           redirect=False
                           )
    # after the init method the main router will navigate to the login form so no need to redirect

```

Then for the `LoginForm`

```python
@routing.route('login')
class LoginForm(LoginFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run when the form opens.
    
  def form_show(self, **event_args):
    """This method is called when the column panel is shown on the screen"""
    user = anvil.users.get_user()
    while not user:
      user = anvil.users.login_with_form()
    
    routing.remove_from_cache(self.url_hash)  # prevents the login form loading from cache in the future... 
    routing.set_url_hash('', 
                         replace_current_url=True,
                         redirect=True
                         )
    # '' replaces 'login' in the history stack and redirects to the HomeForm

```

### Separate from `HashRouting` navigation

Rather than have the `LoginForm` be part of the navigation, you could create a `LoginForm` as a startup form without using any `HashRouting` decorators. 

Then when the user has signed in you can call `open_form('MainForm')`. The `main_router` will then take control of the `url_hash` based navigation. 

When the user signs out you can call `open_form('LoginForm')` and the `main_router` will no longer have control of the navigation. There will still be entries when the user hits back/forward navigation (i.e. the `url_hash` will change but there will be no change in forms...) :smile:

(You will need to add an on_navigation method to the `LoginForm`, which does nothing, to keep HashRouting happy)
```python
def on_navigation(self):
    pass
```

---

## I have a page that is deleted - how do I remove it from the cache?

```python

def trash_link_click(self, **event_args):
  """called when trash_link is clicked removes the """
  self.item.delete()  # table row
  routing.remove_from_cache(self.url_hash) # self.url_hash provided by the @routing.route class decorator
  routing.set_url_hash('articles', 
                        replace_current_url=True,
                      )

```

And in the `__init__` method - you will want something like:

```python
@routing.route('article', keys=['id'], title='Article-{id}')
class ArticleForm(ArticleFormTemplate):
  def __init__(self, **properties):
    try:
      self.item = anvil.server.call('get_article_by_id', self.url_dict['id'])
    except:  
      routing.set_url_hash('articles', replace_current_url=True)
      raise Exception('This article does not exist or has been deleted')
      
```

---

## Form Show is important

since the forms are loaded from cache you may want to use the `form_show` events if there is a state change


### Example 1

When that article was deleted in the above example we wouldn't want the deleted article to show up on the `repeating_panel`

so perhaps:
```python
@routing.route('articles')
class ListArticlesForm(ListArticlesFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.repeating_panel.items = anvil.server.call('get_articles')

    # Any code you write here will run when the form opens.

  def form_show(self, **event_args):
    """This method is called when the column panel is shown on the screen"""
    self.repeating_panel.items = anvil.server.call_s('get_articles')
    # silent call to the server on form show

```

**An alternative approach to the above scenario:**

set `load_from_cache=False`

That way you wouldn't need to utilise the show event of the `ListArticlesForm`


```python
@routing.route('article', keys=['id'], title='Article-{id}')
class ArticleForm(ArticleFormTemplate):
  def __init__(self, **properties):
    try:
      self.item = anvil.server.call('get_article_by_id', self.url_dict['id'])
    except:  
      routing.set_url_hash('articles', replace_current_url=True, load_from_cache=False)

  def trash_link_click(self, **event_args):
    """called when trash_link is clicked removes the """
    self.item.delete()  # table row
    routing.remove_from_cache(self.url_hash) # self.url_hash provided by the @routing.route class decorator
    routing.set_url_hash('articles', 
                         replace_current_url=True, 
                         load_from_cache=False)  
```

**Additional alternative approach to the above scenario:**

use `routing.load_form` instead of `routing.set_url_hash` 

```python
@routing.route('article', keys=['id'], title='Article-{id}')
class ArticleForm(ArticleFormTemplate):
  def __init__(self, **properties):
    try:
      self.item = anvil.server.call('get_article_by_id',self.url_dict['id'])
    except:  
      routing.load_form(ListArticlesForm, replace_current_url=True, load_from_cache=False)

  def trash_link_click(self, **event_args):
    """called when trash_link is clicked removes the """
    self.item.delete()  # table row
    routing.remove_from_cache(self.url_hash) # self.url_hash provided by the @routing.route class decorator
    routing.load_form(ListArticlesForm, 
                      replace_current_url=True, 
                      load_from_cache=False)  

```


### Example 2

In the search example above the same form represents multiple `url_hash`s in the cache.

No problem. 

Whenever navigation is triggered by back/forward button clicks the `self.url_hash`, `self.url_dict` and `self.url_pattern` are updated and the `form_show` event is triggered. 

```python
def form_show(self, **event_args):
  search_text = self.url_dict.get('search','')
  self.search_terms.text = search_text
  self.search(search_text)
```
---

## List of Methods

```python
routing.get_url_components()                          # returns url_hash, url_pattern, url_dict
routing.get_url_hash()                                # returns url_hash as a string
routing.get_url_pattern()                             # returns url_pattern 
routing.get_url_dict()                                # returns url_dict 

routing.remove_from_cache(url_hash)
routing.add_to_cache(url_hash, form)                  # nb:  form should be initiated 
                                                      # e.g. routing.add_to_cache('form1',Form1())  
                                                      # or   routing.add_to_cache('form1', self) 
routing.clear_cache()

routing.set_url_hash(url_hash, **kwargs)              
routing.load_form(form, **properties)                 # nb:  form should NOT be initiated 
                                                      # e.g. routing.load_form(Form1)
routing.load_error_form()                             # loads error_form, adds to cache at current url
```

---

## A Note on `load_form` with Multiple Decorators


```python
@routing.route('home')
@routing.route('')
class Home(HomeTemplate):
```

`routing.load_form(Home)` will raise a `KeyError` since it does not know which `url_pattern` to choose
```python
raise KeyError("Home has multiple decorators - you must provide a url_pattern [and url_keys] with load_form()")
```

Instead do: <br>
`routing.load_form(Home, url_pattern='home')` 
<br>
or
<br>
 `routing.load_form(Home, url_pattern='')`

---

## Routing Debug Print Statements

To debug your routing behaviour use the routing logger. Routing logs are turned off by default.

To use the routing logger, in your `MainForm` do:
```python
from HashRouting import routing

routing.logger.debug = True

@routing.main_router
class MainForm(MainFormTemplate):

```

You can also show the entire log of routing print statements in the following way...

```python
def button_1_click(self, **event_args):
  alert(routing.show_log(), large=True)

```

---

## Leaving the app

Routing implements [W3 Schools onbeforeunload](https://www.w3schools.com/jsref/tryit.asp?filename=tryjsref_onbeforeunload_dom) method.

This warns the user  before navigating away from the app using a default browser warning.
<br>
(does not work on ios) 

By default this setting is switched off. 
<br>
To switch it on do: `routing.set_warning_before_app_unload(True)`

To implement this behaviour for all pages change the setting in your `MainForm` like:

```python
from HashRouting import routing

routing.set_warning_before_app_unload(True)

@routing.main_router
class MainForm(MainFormTemplate):

```
<br>

To implement this behaviour only on specific `Route Forms` toggle the setting like:

```python
def form_show(self, **event_args):
  routing.set_warning_before_app_unload(True)

def form_hide(self, **event_args):
  routing.set_warning_before_app_unload(False)

```

Or based on a parameter (See the example app `ArticleForm` code for a working example)

```python
def edit_status_toggle(status):
  routing.set_warning_before_app_unload(status)

```

*NB:*
When used on a specific `Route Form` this should be used in conjunction with the `before_unload` method (see above).