import docker
from StateStorage import *
CMD="nc -e /bin/cat -l -p 8200"

IMAGE = "nc-ubuntu"

HOST_PORT= 8100
DOC_PORT = '8200/tcp'





if __name__=="__main__":
    client = docker.from_env()
    # client.containers.run(IMAGE, CMD, name="test2", ports={DOC_PORT:HOST_PORT}, detach=True)

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


    print(writeToFile(data, 'storage.json'))

    print(readFromFile('storage.json'))

