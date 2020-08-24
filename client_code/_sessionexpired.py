import anvil as _anvil

class _SessionExpired:
  _reload = False
  @property
  def reload(self):
    return self._reload
  @reload.setter
  def reload(self, value):
    if (not isinstance(value, bool)):
      raise TypeError(f'reload expected a bool not {type(value)}')
    self._reload = value
    _anvil.js.call_js('sessionExpiredHandler', value)
    
SessionExpired = _SessionExpired()