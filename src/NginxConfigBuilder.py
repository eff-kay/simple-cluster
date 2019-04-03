import nginx

filename = 'loadbalancer/nginx.conf'

def create_nginx_config(server):
    c = nginx.Conf()
    e = nginx.Events()
    e.add(nginx.Key('worker_connections', '1024'))
    c.add(e)
    h = nginx.Http()
    u = nginx.Upstream('localhost', nginx.Key('server', server+':3000'))
    h.add(u)
    s = nginx.Server()
    s.add(
        nginx.Key('listen', '8080'),
        nginx.Key('server_name', 'localhost'),
        nginx.Location('/',
                       nginx.Key('proxy_pass', 'http://localhost'),
                       nginx.Key('proxy_set_header', 'Host $host')
                       )
    )
    h.add(s)
    c.add(h)

    nginx.dumpf(c, filename)


