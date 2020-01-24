# HashRouting
HashRouting - a dependancy for anvil.works that allows navigation in apps


---

## Main form

This is the startup form, the one loaded when the app starts. It contains the header, the navigation bar and a content panel where all the other forms will be loaded during the life of the app.

The Main form is **not** the home form. The Main form has no content, only has navigation, header and infrastructure to show all the other forms.

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

## All Route forms

These are all the forms that are loaded inside the main form's content panel.

- Import the routing module and add the decorator that defines the page name and the query string parameters. This shows how to link a form to the URL `<appdomain.com>#article?id=123`:
```python
from HashRouting import routing

@routing.route('article', keys=['id'])
class Article(ArticleTemplate):
```

## Home form

The Home form is the form that appears in the content area of the Main form.

- Import the routing module and add the decorator with the page name set to an empty string
```python
from HashRouting import routing

@routing.route('')
class Home(HomeTemplate):
```

## Error form

This is the form that is shown when the url refers to a page that does not exist or the query string does not match the keys listed in the decorator. 
Follow these steps to create an error form that shows an error message and a button to navigate back to the home page:

- Create a form with a label `Sorry, this page does not exist`

**Optional**
- Add a button with this code on the `button_1_click` method:

```python
    set_url_hash('')
```
- Import the routing module and add the decorator `@routing.error_form`:
```python
from HashRouting import routing

@routing.error_form
class ErrorForm(ErrorFormTemplate):
```

## Navigation

It is important to never use the typical method to navigate when implementing `HashRouting`
```python
# Banned
get_open_form().content_panel.clear()
get_open_form().content_panel.add_component(Home())
# This will result in an Exception('Form1 is a route form and was not loaded from routing')
```

**Instead**
```python
# option 1
set_url_hash('home')

# option 2
routing.load_form(Home, 'home')
```


## Notes

Form definition cannot have required named parameters. Something like this is not allowed:
```python
    @routing.route('form1', keys=['key1'])
    class Form1(Form1Template):
      def __init__(self, key1, **properties):
```
All the parameters listed in `keys` are required, and the rule is enforced by the routing module.
This is the correct way:
```python
    @routing.route('form1', keys=['key1'])
    class Form1(Form1Template):
      def __init__(self, **properties):
        key1 = self.url_dict['key1']  #routing provides self.url_dict
```

---

It is possible to define optional parameters by adding multiple decorators, e.g. one with and one without the key. Here is an example that allows to use the `home page` with the default empty string and with one optional `search` parameter:
```python
    @routing.route('')
    @routing.route('', keys='search')
    class Form1(Form1Template):
      def __init__(self, **properties):
        self.init_components(**properties)
        self.search_terms.text = self.url_dict.get('search', '')
```

---

It is possible to change the current url without adding the new url to the browser history. For example the previous form could have this code:
```python
    def search_click(self, **event_args):
      if self.search_terms.text:
        routing.replace_current_url(f'?search={self.search_terms.text}', replace_in_history=False)
      else:
        routing.replace_current_url(f'',  replace_in_history=False)
      self.search(self.search_terms.text)
```

in the `routing.replace_current_url` method,  `replace_in_history=True` is the defualt

You can also do:
`routing.replace_current_url(url_hash, redirect=True)` which will force routing to navigate to url_hash provided - by default `redirect=False`

---

**Security issue**: You log in, open a form with some data, go to the next form, log out, go back 3 steps and you see the cached stuff that was there when you were logged in.
**Solution**: When a form shows sensitive data it should always check for user permission in the `form_show` event, which is triggered when a cached form is shown.
You can also call `routing._clear_cache()` to remove the cache upon logging out.

___

## Tab Title

You can set each route form to have a title parameter which will change the tab title of the window

If you do not provide a title then the tab title will be the default title provided by anvile

**Examples**:

```python
@routing.route('home', title='Home | RoutingExample')
@routing.route('',     title='Home | RoutingExample')
class Home(HomeTemplate):
```

```python
@routing.route('article', keys=['id'], title="Article-{id} | RoutingExample")
class ArticleForm(ArticleFormTemplate):

# Think `f strings` without the f
# Anything in curly braces should be an item from `keys`
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


  def on_navigation(self, url_hash, url_pattern, url_dict):
    # this method is called whenever routing provides navigation behaviour
    # url_hash, url_pattern, url_dict are provided by the main_router class decorator
    for link in self.links:
      if link.tag.url_hash == url_hash:
        link.role = 'selected'
      else:
        link.role = 'default'
```

___

## Preventing a Form from Closing

if you return a value in the on_navigation method you will stop the form from loading e.g.

```python
  def on_navigation(self, url_hash, url_pattern, url_dict):
    # this method is called whenever routing provides navigation behaviour
    # url_hash, url_pattern, url_dict are provided by the main_router class decorator
    current_form = routing._current_form  #private attribute use with care...
    if current_form.url_pattern == 'edit-article':
      if confirm('are you sure you want to close this form?'):
        pass
      else:
        routing.replace_current_url(current_form.url_hash)  
        return 'STOP'
```

___

## Passing properties to a form

You can pass properties to a form using the `routing.load_form()` method e.g.

```python
routing.load_form(Article,id=3,item=item)

```

___
## Sometimes my Route Form is a Route Form sometimes it is a Component

No problem... use the parameter `route=False` to avoid typical routing behaviour

e.g.

```python
def button_click(self,**event_args):
  alert(ArticleForm(route=False))  
  #setting route = False stops the Route Form using the routing module...
```