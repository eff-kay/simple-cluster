import statistics
import docker

import threading
from SimpleCluster.StateStorage import *
from SimpleCluster.Manager import *
UPPER_LIMIT =25.00
LOWER_LIMIT = 10.00

def calculate_cpu_percent(d, previous_cpu, previous_system):
    # import json
    # du = json.dumps(d, indent=2)
    # logger.debug("XXX: %s", du)
    cpu_percent = 0.0
    cpu_total = float(d["cpu_stats"]["cpu_usage"]["total_usage"])
    cpu_delta = cpu_total - previous_cpu
    cpu_system = float(d["cpu_stats"]["system_cpu_usage"])
    system_delta = cpu_system - previous_system
    online_cpus = d["cpu_stats"].get("online_cpus", len(d["cpu_stats"]["cpu_usage"]["percpu_usage"]))
    if system_delta > 0.0:
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
    #print(cpu_percent, cpu_system, cpu_total)
    return cpu_percent, cpu_total, cpu_system

def get_cpu_percent(container_id):
    global container_state, client

    container = client.containers.get(container_id)
    previous_cpu= container_state[container_id][0]
    previous_system= container_state[container_id][1]

    currenStats = container.stats(decode=True)
    d = next(currenStats)
    cpu_percent, current_cpu, current_system = calculate_cpu_percent(d, previous_cpu, previous_system)

    container_state[container_id]=[current_cpu, current_system]
    return cpu_percent

SCALE_UP_STATBILITY=3
SCALE_DOWN_STATBILITY=1

def start_auto_scaling(app_name, stop_event):
    app_workers = getWorkersForApp(app_name)
    for worker in app_workers:
        container_state[worker]= [0,0]

    scaleup_count = 0
    scaledown_count = 0

    while(True) and not stop_event.is_set():
        cpu_percentage=[]
        # we need to get the updated CPU workers
        app_workers = getWorkersForApp(app_name)
        for worker in app_workers:
            cpu_percentage.append(get_cpu_percent(worker))

        mean_cpu_percentage= statistics.mean(cpu_percentage)
        if mean_cpu_percentage >= UPPER_LIMIT:
            if scaleup_count < SCALE_UP_STATBILITY:
                scaleup_count+=1
                pass
            else:
                scaleup_count=0
                logger.info("scaleup, cpu_percentage: {}".format(mean_cpu_percentage))
                container_id = scale_up(app_name, 1)
                container_state[container_id] = [0, 0]

        if mean_cpu_percentage <= LOWER_LIMIT and len(app_workers) > 1:
            if scaledown_count < SCALE_DOWN_STATBILITY:
                scaledown_count+=1
                pass
            else:
                scaledown_count=0
                logger.info("scaledown, cpu_percentage: {}".format(mean_cpu_percentage))
                container_id = scale_down(app_name, 1)
                del container_state[container_id]


container_state = {}
client = docker.from_env()

if __name__=="__main__":
    app_name='testApp1'
    stop_event=threading.Event()
    start_auto_scaling(app_name, stop_event)









    # parser = argparse.ArgumentParser(description='Specify your app name and command')
    # parser.add_argument('-n', '--name', help='name of the app', required=True)
    # parser.add_argument('-c', '--command', help='scale-up, scale-down, start, list', required=True)
    # args = vars(parser.parse_args())
    #
    # client = docker.from_env()
    #
    # if args['command']=='start':
    #     #you start the thing
    #     container = client.containers.run(IMAGE, CMD, ports={DOC_PORT:HOST_PORT}, detach=True)
    #     nameOfApp = args['name']
    #     storeContainer(nameOfApp, container.id)
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
    #
    # elif args['command']=='list':
    #
    #     containers = client.containers.list(all)
    #
    #     print(list(map(lambda x: x.name+", "+x.status, containers)))