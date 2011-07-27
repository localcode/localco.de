from fabric.api import run


def teststatic():
    print 'Running "findstatic"'
    run('python manage.py findstatic') # should determine which static files would be found.
    print 'Running "collectstatic" as test'
    run('python manage.py collectstatic --dry-run') # should show what files would be copied to which directories

def go(): # just a runserver shortcut
    run('python manage.py runserver')

def webfaction(): # should be used to ssh into webfaction
    pass

