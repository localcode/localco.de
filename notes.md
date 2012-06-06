# NOTES on development and deployment

## To Access Webfaction

On any unix machine, open terminal and use the `ssh` tool to log in to webfaction:

```bash
ssh localcode@localcode.webfactional.com
```

Then enter the password.  
The folder organization at webfaction is organized like so:

```
/home/
    localcode/
        webapps/
            django/
            static/
            media/
```

### Static Files

Static files, such as css, javascript, and icons, can be placed in a few locations during development. They can be placed in static/, or appname/static/. The django commandline command `python manage.py collectstatic` should search through these directories and copy all the needed static files into the directory designated by `STATIC_ROOT`, which is set as `'/Library/WebServer/Documents/static/localcode/'` for local development, and `'/home/localcode/webapps/static/'` for deployment on webfaction.

### Media

Media files are files uploaded by users. Locally, these files will be placed by django into `'/Library/Webserver/Documents/media/localcode/'`, and served from '`http://localhost/media/localcode/'`. In development, media files will be placed into `'/home/localcode/webapps/media/'` and served from `'http://localco.de/media'`.




