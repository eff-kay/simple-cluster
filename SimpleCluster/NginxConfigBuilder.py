import nginx

CONFIG_DIR = 'loadbalancer/configs/'

def create_nginx_config(nginx_port, app_name, app_server_ip_addr):
    c = nginx.Conf()
    e = nginx.Events()
    e.add(nginx.Key('worker_connections', '1024'))
    c.add(e)
    h = nginx.Http()

    u = nginx.Upstream(app_name)

    u.add(nginx.Key('server', str(app_server_ip_addr) + ':3000'))
    h.add(u)

    s = nginx.Server()
    s.add(
        nginx.Key('listen', str(nginx_port)),
        nginx.Key('server_name', app_name),
        nginx.Location('/',
                       nginx.Key('proxy_pass', 'http://'+app_name),
                       nginx.Key('proxy_set_header', 'Host $host')
                       )
    )

    h.add(s)
    c.add(h)

    nginx.dumpf(c, CONFIG_DIR+app_name+'/nginx.conf')


def add_server(app_name, app_server_ip_addr):

    c = nginx.loadf(CONFIG_DIR+app_name+'/nginx.conf')

    h = c.filter('Http')[0]
    c.remove(h)

    u = h.filter('Upstream')[0]
    h.remove(u)

    u.add(nginx.Key('server', str(app_server_ip_addr) + ':3000'))

    h.add(u)
    c.add(h)

    nginx.dumpf(c, CONFIG_DIR+app_name+'/nginx.conf')


def remove_server(app_name, app_server_ip_addr):

    #creating a new config file everytime
    c = nginx.loadf(CONFIG_DIR+app_name+'/nginx.conf')

    h = c.filter('Http')[0]
    c.remove(h)

    u = h.filter('Upstream')[0]
    h.remove(u)

    u_upd = nginx.Upstream(app_name)

    for k in u.filter('Key'):
        if not k.value == str(app_server_ip_addr) + ':3000':
            u_upd.add(k)

    h.add(u_upd)
    c.add(h)

    nginx.dumpf(c, CONFIG_DIR+app_name+'/nginx.conf')
