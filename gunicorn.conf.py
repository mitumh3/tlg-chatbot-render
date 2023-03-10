
# Set the number of Gunicorn worker processes
workers = 1

# Set the worker class to use
worker_class = 'gevent'

# Set the maximum number of requests each worker will process before restarting
max_requests = 1000

# Set the timeout for worker processes to gracefully exit after receiving a SIGTERM signal
timeout = 1800

# Set the name of the Python module that contains the WSGI application object
# In this case, the module is 'bot' and the WSGI application object is 'bot:app'
# where 'app' is a reference to the underlying Telegram client instance
# If you've defined a different attribute name for your Telegram client instance, update the value accordingly
# This tells Gunicorn to use the 'app' attribute of the 'bot' module as the WSGI application object
# and to serve it using the specified configuration settings
module_name = 'bot'
app_name = 'client'
