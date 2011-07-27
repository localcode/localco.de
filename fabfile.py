from fabric.api import run, env

def localhost():
    env.hosts = ['localhost']

def webfaction(): # should be used to ssh into webfaction
    env.hosts = ['localcode@localcode.webfaction.com']

def teststatic():
    run('python manage.py collectstatic --dry-run -i "*/lib/*"')

def testfab():
    run('pwd')

def deploy():
    print 'deploy time'
    pass

