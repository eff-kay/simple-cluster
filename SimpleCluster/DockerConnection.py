import docker
import argparse

from StateStorage import *
CMD="nc -e /bin/cat -l -p 8200"

IMAGE = "nc-ubuntu"

HOST_PORT= 8100
DOC_PORT = '8200/tcp'


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Specify your app name and command')
    parser.add_argument('-n', '--name', help='name of the app', required=True)
    parser.add_argument('-c', '--command', help='scale-up, scale-down, start, list', required=True)
    args = vars(parser.parse_args())

    client = docker.from_env()

    if args['command']=='start':
        #you start the thing
        container = client.containers.run(IMAGE, CMD, ports={DOC_PORT:HOST_PORT}, detach=True)
        nameOfApp = args['name']
        storeContainer(nameOfApp, container.id)

    elif args['command']=='scale-up':
        #you scale the thing
        print("sinide this")

    elif args['command']=='scale-down':
        # you scale the thing

        #you scale the thing
        print("sinide this")

        # nameOfApp = args['name']
        #
        # client.containers.get(nameOfApp)
        # print("sinide this")

    elif args['command']=='list':
        # nameOfApp = args['name']
        # children = getContainers(nameOfApp)
        # print(list(map( lambda x: x.value, children)))

        containers = client.containers.list(all)

        print(list(map(lambda x: x.name+", "+x.status, containers)))





    # children = getContainers('abc')
    # print(list(map( lambda x: x.value, children)))
    #
    # client = docker.from_env()
    #

    #
    #
# )

    #
    # parser.add_argument("")
    # client = docker.from_env()
    #
    #
    #
    # print(writeToFile(data, 'storage.json'))
    #
    # print(readFromFile('storage.json'))

    # containers = client.containers.list(all)
    #
    # for c in containers:
    #     print(c.name, c.status)

    # data = {}
    #
    # data['s'] = []
    #
    # data['s'].append({
    #     'name': 'test'
    # })
    #
    # data['s'].append({
    #     'anotherName': 'test1'
    # })




