#!/usr/bin/env python
# from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple
from monkeybook import app
# from monkeybook import app, api_app

# This allows us to run two separeate
# WSGI apps on two different url prefixes
# application = DispatcherMiddleware(app, {
#     '/api': api_app
# })

# run_simple('localhost', 5000, application,
run_simple('localhost', 5000, app,
           use_reloader=True, use_debugger=True, use_evalex=True)

