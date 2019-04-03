import docker
import logging
import socket
import os

from src.NginxConfigBuilder import create_new_nginx_config, add_server

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(threadName)s %(levelname)s %(message)s')

# docker build -t backend backend
# docker build -t loadbalancer loadbalancer


def get_free_port():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('localhost', 0))
  addr, port = s.getsockname()
  s.close()
  return port


if __name__=="__main__":

    client = docker.from_env()
    active_apps = {}
    IMAGE_APP = "testapp8"
    IMAGE_LB = "loadbalancer3"

    create_new_nginx_config()


    while(True):

        command = input("Next command: ").split(' ')

        if (command[0] == 'start'):

            assert (len(command) == 2), "Incorrect format. Enter \"start\" <app_name>"

            app_name = command[1]

            if(app_name in active_apps.keys()):
                logger.info("App %s already running" % app_name)
                continue

            container_app = client.containers.run(IMAGE_APP, "python app.py", name=app_name+"-1", stderr=True, stdin_open=True, remove=True, detach=True)

            port = get_free_port()
            add_server(port, app_name+"-1")
            container_lb = client.containers.run(IMAGE_LB, tty=True, stderr=True, stdin_open=True, ports={str(port)+'/tcp': port},
                                               name=app_name+"-loadbalancer", remove=True, detach=True,
                                               volumes={os.getcwd()+'/loadbalancer': {'bind': '/etc/nginx', 'mode': 'ro'}},
                                               links={app_name+"-1": app_name+"-1"})

            container_lb.exec_run('nginx -s reload')

            active_apps[app_name] = [container_lb, container_app]

            logger.info("App %s started. Port chosen is: %d" % (app_name, port))


        elif (command[0] == 'stop'):
            assert (len(command) == 2), "Incorrect format. Enter \"stop\" <app_name>"
            app_name = command[1]

            if(app_name not in active_apps.keys()):
                logger.info("App % is not active" % app_name)
                continue

            for container in active_apps[app_name]:
                container.stop(timeout=0)

            logger.info("App %s stopped. All containers destroyed" % (app_name))

        elif (command[0] == 'scaleup'):
            pass

        elif (command[0] == 'scaledown'):
            pass



    # parser = argparse.ArgumentParser(description='Specify your app name and command')
    # parser.add_argument('-n', '--name', help='name of the app', required=True)
    # parser.add_argument('-c', '--command', help='scale-up, scale-down, start, list', required=True)
    # args = vars(parser.parse_args())
    #
    # client = docker.from_env()
    #
    # if args['command']=='start':
    #     #you start the thing
    #     container = client.containers.run(IMAGE, CMD, ports={DOC_PORT:HOST_PORT}, remove=True, detach=True)
    #     nameOfApp = args['name']
    #     #storeContainer(nameOfApp, container.id)
    #
    # elif args['command']=='scale-up':
    #     #you scale the thing
    #     print("sinide this")
    #
    # elif args['command']=='scale-down':
    #     # you scale the thing
    #
    #     #you scale the thing
    #     print("sinide this")
    #
    #     # nameOfApp = args['name']
    #     #
    #     # client.containers.get(nameOfApp)
    #     # print("sinide this")
    #
    # elif args['command']=='list':
    #     # nameOfApp = args['name']
    #     # children = getContainers(nameOfApp)
    #     # print(list(map( lambda x: x.value, children)))
    #
    #     containers = client.containers.list(all)
    #
    #     print(list(map(lambda x: x.name+", "+x.status, containers)))
