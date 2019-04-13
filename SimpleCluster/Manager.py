import sys
import docker
import logging
import socket
import os
import shutil

from SimpleCluster.NginxConfigBuilder import *
from SimpleCluster.StateStorage import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(threadName)s %(levelname)s %(message)s')

CONFIG_DIR = 'loadbalancer/configs/'

LB = "loadbalancer"
SERVERS = "servers"
ADDR = "address"

IMAGE_APP = "hasnainmamdani/comp598_proj_testapp"
IMAGE_LB = "hasnainmamdani/comp598_proj_loadbalancer"

def get_free_port():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('localhost', 0))
  addr, port = s.getsockname()
  s.close()
  return port


# def rebuild_existing_state():


if __name__=="__main__":

    client = docker.from_env()

    # container_state_file = open("../containerState.p", "rb")

    active_apps={}

    # try:
    #     active_apps= pickle.load(container_state_file)
    # except EOFError:
    #     # file does not exist create one
    #     active_apps={}
    #     container_state_file = open("../containerState.p", "wb+")
    #     pickle.dump(active_apps, container_state_file)


    # localhost for now
    ip_addr = socket.gethostbyname('localhost')

    # shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    # os.mkdir(CONFIG_DIR)

    while True:

        command = input("Next command: ").split(' ')

        if command[0] == 'start':

            if len(command) != 2:
                logger.info("Incorrect format. Enter \"start <app_name>\"")
                continue

            app_name = command[1]

            running_containers = getWorkersForApp(app_name)

            if running_containers:
                logger.info("App %s already running" % app_name)

            else:
                container_app = client.containers.run(IMAGE_APP, "python app.py", stderr=True, stdin_open=True, remove=True, detach=True)
                saveAppState(app_name, container_app.id)


                container_app_ip_addr = client.containers.get(container_app.id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                port = get_free_port()
                os.mkdir(CONFIG_DIR+app_name)
                create_nginx_config(port, app_name, container_app_ip_addr)
                container_lb = client.containers.run(IMAGE_LB, tty=True, stderr=True, stdin_open=True, ports={str(port)+'/tcp': port},
                                                   name=app_name+"-loadbalancer", remove=True, detach=True,
                                                   volumes={os.getcwd()+'/'+CONFIG_DIR+app_name: {'bind': '/etc/nginx', 'mode': 'ro'}})
                container_lb.exec_run('nginx -s reload')

                saveLbState(app_name, container_lb.id)

                logger.info("Application %s started with one worker at %s:%d" % (app_name, ip_addr, port))

        elif command[0] == 'stop':
            if len(command) != 2:
                logger.info("Incorrect format. Enter \"stop <app_name>\"")
                continue

            app_name = command[1]

            running_containers = getWorkersForApp(app_name)
            if not running_containers:
                logger.info("Application % is not active" % app_name)
                continue

            for container_id in running_containers:
                try:
                    client.containers.get(container_id).stop(timeout=0)
                except:
                    pass

            load_balancer_id = getLbForApp(app_name)

            if load_balancer_id:
                try:
                    client.containers.get(load_balancer_id).stop(timeout=0)
                except:
                    pass

            deleteLbState(app_name)
            deleteAppState(app_name)


            #TODO: add this again when fault tolerance is added
            shutil.rmtree(CONFIG_DIR+app_name)

            logger.info("Application %s stopped. All relevant containers destroyed" % (app_name))

        elif command[0] == 'scaleup':

            if len(command) != 3:
                logger.error("Incorrect format. Enter \"scaleup <app_name> <num_workers>\"")
                continue

            app_name = command[1]
            num_workers = int(command[2])

            running_containers = getWorkersForApp(app_name)
            if not running_containers:
                logger.error("App % is not active" % app_name)
                continue

            if num_workers < 1:
                logger.error("Invalid number of worker to add = %d. It should be greater than zero. Skipping." %(num_workers))
                continue

            for i in range(num_workers):
                container_app = client.containers.run(IMAGE_APP, "python app.py", stderr=True, stdin_open=True, remove=True, detach=True)
                container_app_ip_addr = client.containers.get(container_app.id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                add_server(app_name, container_app_ip_addr)

                saveAppState(app_name, container_app.id)
            container_lb = client.containers.get(app_name+"-loadbalancer")
            container_lb.exec_run('nginx -s reload')
            saveLbState(app_name, container_lb.id)

            logger.info("Added %d more workers to the application %s. Total workers now = %d" % (num_workers, app_name, len(running_containers)+num_workers))

        elif command[0] == 'scaledown':

            if len(command) != 3:
                logger.error("Incorrect format. Enter \"scaledown <app_name> <num_workers>\"")
                continue

            app_name = command[1]
            num_workers = int(command[2])

            running_containers = getWorkersForApp(app_name)
            if not running_containers:
                logger.error("Application % is not active" % app_name)
                continue

            if num_workers < 1:
                logger.error("Invalid number of worker to remove = %d. It should be greater than zero. Skipping." %(num_workers))
                continue

            if len(running_containers) <= num_workers:
                logger.error("User intended to remove all workers. Consider stopping the application with the 'stop' command.")
                continue

            for i in range(num_workers):
                container_id= running_containers.pop()
                container_app_ip_addr = client.containers.get(container_id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                client.containers.get(container_id).stop(timeout=0)
                remove_server(app_name, container_app_ip_addr)

                deleteWorkerforApp(app_name, container_id)

            container_lb = client.containers.get(app_name+"-loadbalancer")
            container_lb.exec_run('nginx -s reload')

            logger.info("Removed %d workers from the application %s. Total workers now = %d" % (num_workers, app_name, len(running_containers)-num_workers))

        elif command[0] == 'list':
            if len(command) != 2:
                logger.info("Incorrect format. Enter \"list <app_name>\"")
                continue

            app_name = command[1]

            runningWorkerIds = getWorkersForApp(app_name)
            if not runningWorkerIds:
                print("{0} application is not running".format(app_name))
            # stop all workers and the load balancer
            else:
                print("{} workers running for {}".format(len(runningWorkerIds), app_name))
                print("Container Ids")
                for worker in runningWorkerIds:
                    print(worker)


        elif command[0] == 'exit':
            # with open("../containerState.p",'wb+') as cs:
            #     pickle.dump(active_apps, cs)

            sys.exit(0)

        else:
            logger.error("Invalid command")
