# Simple Http Library
This repo contans a simple, convenient API for working with Http.
It enables who uses it to easily set up a basic Http server.


## How To Use
First of all you have to download the httplib.py file. After you've
downloaded the file just put it in your project's directory.
Now let's say we would like to host an http server on our computer
using the api.


* First, we need to create a directory that will contain our website.
  This directory must be called 'webroot' so the api will recognize
  it. In case you want it to be recognized otherwise just get to the
  httplib.py and replace 'webroot' with '\[YourNewName\]'.

* After created the folder that contains our website, now we need to
  create a new python file, this file will run the server.

* Now write within the file:
```python
from httplib import HttpServer


server = HttpServer('0.0.0.0', 8000)
server.run()  # run the server
```

* All that's left to do is just run the file.
In order to make sure that the server actually works you should
open the browser and type in the url box: 127.0.0.1:8000
and see if you hop into your website.

