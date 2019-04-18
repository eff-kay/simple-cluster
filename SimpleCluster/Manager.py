import sys
import docker
import logging
import socket
import os
import shutil
import threading
import asyncio
import time

from SimpleCluster.NginxConfigBuilder import *
from SimpleCluster.StateStorage import *
from SimpleCluster.AutoScaling import *

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


def scale_up(app_name, num_workers):
    client = docker.from_env()
    running_containers = getWorkersForApp(app_name)

    for i in range(num_workers):
        container_app = client.containers.run(IMAGE_APP, "python app.py", stderr=True, stdin_open=True, remove=True,
                                              detach=True)
        container_app_ip_addr = client.containers.get(container_app.id).attrs['NetworkSettings']['Networks']['bridge'][
            'IPAddress']
        add_server(app_name, container_app_ip_addr)

        saveAppState(app_name, container_app.id)
    container_lb = client.containers.get(app_name + "-loadbalancer")
    container_lb.exec_run('nginx -s reload')

    logger.info("Added %d more workers to the application %s. Total workers now = %d" % (
    num_workers, app_name, len(running_containers) + num_workers))

    return container_app.id

def scale_down(app_name, num_workers):

    client = docker.from_env()
    running_containers = getWorkersForApp(app_name)

    if num_workers < 1:
        logger.error(
            "Invalid number of worker to remove = %d. It should be greater than zero. Skipping." % (num_workers))
        return

    if len(running_containers) <= num_workers:
        logger.error("User intended to remove all workers. Consider stopping the application with the 'stop' command.")
        return

    for i in range(num_workers):
        container_id = running_containers.pop()
        container_app_ip_addr = client.containers.get(container_id).attrs['NetworkSettings']['Networks']['bridge'][
            'IPAddress']
        client.containers.get(container_id).stop(timeout=0)
        remove_server(app_name, container_app_ip_addr)

        deleteWorkerforApp(app_name, container_id)

    container_lb = client.containers.get(app_name + "-loadbalancer")
    container_lb.exec_run('nginx -s reload')

    logger.info("Removed %d workers from the application %s. Total workers now = %d" % (
    num_workers, app_name, len(running_containers)))

    return container_id

def house_cleaning():
    while True:
        client = docker.from_env()
        all_live_containers = client.containers.list(all)

        all_live_containers= [x.id for x in all_live_containers]
        current_apps = getTotalApps()

        for app in current_apps:
            for container_id in getWorkersForApp(app):
                if container_id not in all_live_containers:
                    #start a new container if it died during the manager restart
                    deleteWorkerforApp(app, container_id)
                    scale_up(app, 1)
        time.sleep(10)
@asyncio.coroutine
def main_shell():
    client = docker.from_env()

    autoscaling_stop_events ={}

    #populate stop events
    current_apps= getTotalApps()
    for app in current_apps:
        autoscale_status = getAutoScaleStatus(app)
        if autoscale_status=='auto':
            stop_event = threading.Event()
            # start the auto scaler thread
            t = threading.Thread(name=app+"_autoscaling", target=start_auto_scaling, daemon=True, args=(app,stop_event))
            t.start()
            autoscaling_stop_events[app]=stop_event


    # localhost for now
    ip_addr = socket.gethostbyname('localhost')

    while True:
        try:
            command = input("Next command: ").split(' ')

            if command[0]=='clean-slate':
                apps = getTotalApps()
                for app in apps:
                    deleteAppState(app)
                    shutil.rmtree(CONFIG_DIR + app)

            elif command[0] == 'start':

                if len(command) != 2:
                    logger.info("Incorrect format. Enter \"start <app_name>\"")
                    continue

                try:
                    app_name = command[1]
                    if app_name=='':
                        logger.info("Incorrect format. Enter \"start <app_name>\"")
                        continue
                except:
                    logger.info("Incorrect format. Enter \"start <app_name>\"")
                    continue

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

                    saveLbState(app_name, container_lb.id, port)
                    setAutoScaleStatus(app_name, 'manual')
                    logger.info("Application %s started with one worker at %s:%d" % (app_name, ip_addr, port))

            elif command[0] == 'stop':
                if len(command) != 2:
                    logger.info("Incorrect format. Enter \"stop <app_name>\"")
                    continue

                try:
                    app_name = command[1]

                    if app_name=="":
                        logger.info("Incorrect format. Enter \"stop <app_name>\"")
                        continue
                except:
                    logger.info("Incorrect format. Enter \"stop <app_name>\"")
                    continue



                running_containers = getWorkersForApp(app_name)
                if not running_containers:
                    logger.info("Application %s is not active" % app_name)
                    continue

                autoscale_status = getAutoScaleStatus(app_name)

                if autoscale_status=='auto':
                    autoscaling_stop_events[app_name].set()
                    logger.info("autoscaling for {} stopped".format(app_name))

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
                deleteAutoScaleStatus(app_name)
                deleteLbState(app_name)
                deleteAppState(app_name)

                shutil.rmtree(CONFIG_DIR+app_name)

                logger.info("Application %s stopped. All relevant containers destroyed" % (app_name))

            elif command[0] == 'scaleup':

                if len(command) != 3:
                    logger.error("Incorrect format. Enter \"scaleup <app_name> <num_workers>\"")
                    continue


                try:
                    app_name = command[1]
                    num_workers = int(command[2])

                    if app_name=="" or num_workers=='':
                        logger.error("Incorrect format. Enter \"scaleup <app_name> <num_workers>\"")
                        continue
                except:
                    logger.error("Incorrect format. Enter \"scaleup <app_name> <num_workers>\"")
                    continue


                running_containers = getWorkersForApp(app_name)
                if not running_containers:
                    logger.error("App % is not active" % app_name)
                    continue

                if num_workers < 1:
                    logger.error("Invalid number of worker to add = %d. It should be greater than zero. Skipping." %(num_workers))
                    continue

                autoscale_status = getAutoScaleStatus(app_name)
                if autoscale_status=='auto':
                    logger.error("Autoscale mode enabled, disable it by running \'stop-autosclaing <app_name> \'")
                    continue

                for i in range(num_workers):
                    container_app = client.containers.run(IMAGE_APP, "python app.py", stderr=True, stdin_open=True, remove=True, detach=True)
                    container_app_ip_addr = client.containers.get(container_app.id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                    add_server(app_name, container_app_ip_addr)

                    saveAppState(app_name, container_app.id)
                container_lb = client.containers.get(app_name+"-loadbalancer")
                container_lb.exec_run('nginx -s reload')

                logger.info("Added %d more workers to the application %s. Total workers now = %d" % (num_workers, app_name, len(running_containers)+num_workers))

            elif command[0] == 'scaledown':

                if len(command) != 3:
                    logger.error("Incorrect format. Enter \"scaledown <app_name> <num_workers>\"")
                    continue

                try:
                    app_name = command[1]
                    num_workers = int(command[2])

                    if app_name=="" or num_workers=='':
                        logger.error("Incorrect format. Enter \"scaledown <app_name> <num_workers>\"")
                        continue

                except:
                    logger.error("Incorrect format. Enter \"scaledown <app_name> <num_workers>\"")
                    continue

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


                autoscale_status = getAutoScaleStatus(app_name)
                if autoscale_status=='auto':
                    logger.error("Autoscale mode enabled, disable it by running \'stop-autosclaing <app_name> \'")
                    continue

                for i in range(num_workers):
                    container_id= running_containers.pop()
                    container_app_ip_addr = client.containers.get(container_id).attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
                    client.containers.get(container_id).stop(timeout=0)
                    remove_server(app_name, container_app_ip_addr)

                    deleteWorkerforApp(app_name, container_id)

                container_lb = client.containers.get(app_name+"-loadbalancer")
                container_lb.exec_run('nginx -s reload')

                logger.info("Removed %d workers from the application %s. Total workers now = %d" % (num_workers, app_name, len(running_containers)))

            elif command[0] == 'list':
                if len(command) != 2:
                    logger.info("Incorrect format. Enter \"list <app_name>\"")
                    continue

                try:
                    app_name = command[1]
                    if app_name=="":
                        logger.info("Incorrect format. Enter \"list <app_name>\"")
                        continue
                except:
                    logger.info("Incorrect format. Enter \"list <app_name>\"")
                    continue

                runningWorkerIds = getWorkersForApp(app_name)
                if not runningWorkerIds:
                    print("{0} application is not running".format(app_name))
                # stop all workers and the load balancer
                else:
                    autoscale_status = getAutoScaleStatus(app_name)
                    port = getLBPortForApp(app_name)
                    print("{} ip-address: {}, autoscale-status: {}".format(app_name, ip_addr+":"+port, autoscale_status))
                    print("{} workers running for {}".format(len(runningWorkerIds), app_name))
                    print("Container Ids")
                    for worker in runningWorkerIds:
                        print(worker)


            elif command[0] == 'exit':
                loop.stop()

            elif command[0] == 'ps':
                total_apps = getTotalApps()
                if len(total_apps)==0:
                    print("{0} applications running".format(0))
                # stop all workers and the load balancer
                else:
                    for app in total_apps:
                        print(app)

            elif command[0] == 'ip-address':
                if len(command) != 2:
                    logger.info("Incorrect format. Enter \"ip-address <app_name>\"")
                    continue

                try:
                    app_name = command[1]

                    if app_name=="":
                        logger.info("Incorrect format. Enter \"ip-address <app_name>\"")
                        continue
                except:
                    logger.info("Incorrect format. Enter \"ip-address <app_name>\"")
                    continue

                runningWorkerIds = getWorkersForApp(app_name)
                if not runningWorkerIds:
                    print("{0} application is not running".format(app_name))
                # stop all workers and the load balancer
                else:
                    port = getLBPortForApp(app_name)
                    print("ip address for {} is {}".format(app_name, ip_addr+":"+port))

            elif command[0] == 'start-autoscaling':
                if len(command) != 2:
                    logger.info("Incorrect format. Enter \"start-autoscaling <app_name>\"")
                    continue

                try:
                    app_name = command[1]
                    if app_name=="":
                        logger.info("Incorrect format. Enter \"start-autoscaling <app_name>\"")
                        continue
                except:
                    logger.info("Incorrect format. Enter \"list <app_name>\"")
                    continue

                runningWorkerIds = getWorkersForApp(app_name)
                if not runningWorkerIds:
                    print("{0} application is not running".format(app_name))
                    continue

                autoscale_status = getAutoScaleStatus(app_name)
                if autoscale_status=='auto':
                    logger.error("Autoscale mode already enabled, disable it by running \'stop-autosclaing <app_name> \'")
                    continue

                stop_event = threading.Event()
                # start the auto scaler thread
                t = threading.Thread(name=app_name+"_autoscaling", target=start_auto_scaling, daemon=True, args=(app_name,stop_event))
                t.start()

                autoscaling_stop_events[app_name]=stop_event

                setAutoScaleStatus(app_name, 'auto')
                logger.info("autoscaling for {} enabled".format(app_name))

            elif command[0] == 'stop-autoscaling':
                if len(command) != 2:
                    logger.info("Incorrect format. Enter \"stop-autoscaling <app_name>\"")
                    continue

                try:
                    app_name = command[1]
                except:
                    logger.info("Incorrect format. Enter \"list <app_name>\"")
                    continue

                autoscale_status = getAutoScaleStatus(app_name)
                if autoscale_status=='manual':
                    logger.error("Autoscale mode disabled, enable it by running \'start-autosclaing <app_name> \'")
                    continue

                autoscaling_stop_events[app_name].set()
                setAutoScaleStatus(app_name, 'manual')
                logger.info("autoscaling for {} stopped".format(app_name))


            elif command[0]== 'help':
                print("start")
                print("stop")
                print("scaleup")
                print("scaledown")
                print("list")
                print("exit")
                print("ps")
                print("ip-address")
                print("start-autoscaling")
                print("stop-autoscaling")


            else:
                logger.error("Invalid command, try \'help\' to get the list of commands")
        except:
            logger.error("Invalid command, try \'help\' for a list of commands")

if __name__=="__main__":
    house_cleaning_thread = threading.Thread(name="house_cleaning", target=house_cleaning, daemon=True)
    house_cleaning_thread.start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([main_shell()]))