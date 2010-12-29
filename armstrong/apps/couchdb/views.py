from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
import httplib2

def build_url(type, name, couch_url=None, design_doc=None):
    # This checks to see if a ``couch_url`` was provided.  If not, grab
    # the ``COUCH_DEFAULT_URL`` from settings and use it.  On the off
    # chance that we were not explicitly provided with a ``couch_url``
    # and there is not configured default we raise the
    # ``django.core.exceptions.ImproperlyConfigured`` exception
    # explaining the issue to our unfortunate developer.
    if not couch_url:
        if not hasattr(settings, 'COUCH_DEFAULT_URL'):
            msg = "Please either explicitly provide a couch_url or add COUCH_DEFAULT_URL to your settings"
            raise ImproperlyConfigured(msg)

        couch_url = settings.COUCH_DEFAULT_URL

    # Once we have a 
    if couch_url.find("/") == -1:
        couch_url = "http://127.0.0.1:5984/%s" % couch_url

    # Use the configured ``COUCH_DEFAULT_DESIGN_DOC`` when no
    # ``design_doc`` has been provided.
    if not design_doc:
        if not hasattr(settings, "COUCH_DEFAULT_DESIGN_DOC"):
            msg = "Missing design_doc or settings.COUCH_DEFAULT_DESIGN_DOC"
            raise ImproperlyConfigured(msg)
        design_doc = settings.COUCH_DEFAULT_DESIGN_DOC

    # Once we have a design document, either from being explicitly
    # provided or being extracted from settings, we check it to see if
    # it contains a slash and append ``_design/`` if one isn't present.
    if design_doc.find("/") == -1:
        design_doc = "_design/%s" % design_doc

    # The various type of design documents need to be prefixed with an
    # underscore.  We now add the ``_`` if it is not already there.
    type = type[0] == "_" and type or "_%s" % type

    # Finally, we join all of the values we have together, separating
    # them by a forward slash and then return it.
    return "/".join((couch_url, design_doc, type, name))

def raw_request(type):
    # Create an ``http`` variable to be used by ``actual_view`` when
    # making requests.  It is done here to avoid having to re-create it
    # on each request, while still keeping it out of the module level.
    http = httplib2.Http()

    # Here we define the view that is going to be executed by Django.
    # This receives Django's ``request`` parameter first, then all of
    # the variables that are passed in via the view.  The only value
    # that is explicitly required as part of the view is the ``name``.
    def actual_view(request, name, couch_url=None, design_doc=None, template_name=None, relay_params=False):
        # Delegate to ``build_url`` to determine the full URL that
        # should be requested.  Note that ``couch_url`` and
        # ``design_doc`` may be ``None``.  At this point, that is ok as
        # ``build_url`` will fill them in with their correct values or
        # raise the appropriate exception if it can not determine their
        # value.
        url = build_url(type, name, couch_url, design_doc)

        # By default, we do not pass the GET parameters to the CouchDB
        # view, but it can be useful to.  If the ``relay_params`` is set
        # to ``True`` we add them to the value.
        if relay_params:
            url = "%s?%s" % (url, request.META['QUERY_STRING'])

        # Now send the request.  All requests to CouchDB via this are
        # done as ``GET`` requests.  It might make sense to support
        # other types of requests in the future, but for now we're
        # keeping it simple (stupid).
        #
        # The response from ``request`` is a tuple.  The first value is
        # a dict-like object containing the response values, the second
        # is the raw body that was sent.
        response, body = http.request(url, "GET")

        # Now we need to process the response.  First we check to see if
        # this was a valid response.  Anything that is not a ``200`` is
        # treated as an error state and the appropriate response is
        # generated and returned to the client.
        #
        # Special care is taken with 404 responses and Django deviates
        # with those and expects a ``django.http.Http404`` exception to
        # be raised to trigger the default 404 handling.
        if response.status != 200:
            if response.status == 404:
                raise Http404()
            return HttpResponse(status=response.status)

        # We finally have a valid response from Couch.  Before we can
        # hand it off to Django's template engine and render the
        # results, we need to check its type and determine what to do
        # with it.
        #
        # CouchDB returns ``text/plain`` as its Content-Type when
        # returning JSON so we will assume that response type.  It is
        # the CouchDB designer's responsibility to set a proper
        # Content-Type when creating a show that do not emit JSON.
        #
        # Here we attempt to load the JSON string into its Python
        # equivalent.  We swallow all ``ValueError`` exceptions that are
        # generated because we're unable to parse the body.  This
        # assumes that errors parsing are due to a non-JSON response
        # that still returns ``text/plain``.
        if response["content-type"].split(';')[0] == "text/plain":
            try:
                body = json.loads(body)
            except ValueError, e:
                if e.message != "No JSON object could be decoded":
                    raise e

        # The final pieces of setup required is to set the
        # ``template_name`` if needed.  This can be passed to the view
        # via a variable inside the ``urls`` setup, but when it is
        # absent we default to ``armstrong/apps/couchdb/<view>.html``.
        if not template_name:
            template_name = "armstrong/apps/couchdb/%s.html" % type

        # Now we're ready to render and return a response.  This adds a
        # ``RequestContext`` so all context processors are available
        # inside the template.
        context = {"response": response, "body": body}
        return render_to_response(template_name, context,
                                  context_instance=RequestContext(request))

    # Now that the ``actual_view`` is defined, it's time to return it to
    # be used throughout.
    return actual_view

# Define the three views that are available to be used.  Each variable
# is equal to the ``actual_view`` function defined inside
# ``raw_request``.  This style of enclosure allows us to share state
# through closures rather than objects.
list = raw_request('list')
show = raw_request('show')
view = raw_request('view')

