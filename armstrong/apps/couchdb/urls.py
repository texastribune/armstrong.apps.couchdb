# Provides some basic defaults for passing requests straight through to
# CouchDB with minimal settings.  Using these ``urlpatterns`` requires a
# configured ``settings`` module with the default values.

# Import the pieces of Django's URL system that we're going to use.
from django.conf.urls.defaults import patterns, url

# Define a template string that all URLs will match against.  This needs
# to have the type injected into it.  Using this regular expression, we
# extract the name value and pass it to the view.
URL_PATTERN = r'%s/(?P<name>.*)$'

# The default parameters we want to pass are only ``relay_params`` set
# to ``True``.  All other parameters are assumed to be the default.
DEFAULT_PARAMS = {"relay_params": True}

# Now we need to create a way to generate all of the matching URLs.
# This function takes any number of parameters, and generates a matching
# ``django.conf.urls.default.url`` value for it, returning all of the
# values as a list.
def generate_view_pattern(*types):
    return [url(URL_PATTERN % a, a, DEFAULT_PARAMS) for a in types]

# Now we define a ``urlpatterns`` for Django to consume.  We assume that
# we're relaying all GET parameters and doing little else.  These also
# assume the default templates.
#
# This uses the ``generate_view_pattern`` above to generate all of the
# views needed to provide the basic patterns to match ``list``,
# ``show``, and ``view``.
urlpatterns = patterns('armstrong.apps.couchdb.views',
                       *generate_view_pattern('list', 'show', 'view'))
