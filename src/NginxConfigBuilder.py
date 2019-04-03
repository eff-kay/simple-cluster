import nginx

filename = 'loadbalancer/nginx.conf'

def create_new_nginx_config():
    c = nginx.Conf()
    e = nginx.Events()
    e.add(nginx.Key('worker_connections', '1024'))
    c.add(e)
    h = nginx.Http()
    u = nginx.Upstream('localhost')
    h.add(u)
    c.add(h)

    nginx.dumpf(c, filename)

def add_server(nginx_port, app_server):
    c = nginx.loadf(filename)

    h = c.filter('Http')[0]
    c.remove(h)

    u = h.filter('Upstream')[0]
    h.remove(u)

    u.add(nginx.Key('server', app_server+':3000'))
    h.add(u)

    s = nginx.Server()
    s.add(
        nginx.Key('listen', str(nginx_port)),
        nginx.Key('server_name', 'localhost'),
        nginx.Location('/',
                       nginx.Key('proxy_pass', 'http://localhost'),
                       nginx.Key('proxy_set_header', 'Host $host')
                       )
    )

    h.add(s)
    c.add(h)

    nginx.dumpf(c, filename)

