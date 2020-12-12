import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 500 
loglevel = "INFO"
capture_output = True
accesslog = "-"