import json
import os
import etcd

def readFromFile(fileName):
    with open(fileName, 'r') as infile:
        test = json.load(infile)
        return test


def writeToFile(data, fileName):

    try:
        with open(fileName) as f:
            loadData = json.load(f)

        loadData.update(data)

        with open(fileName, 'w') as f:
            json.dump(loadData, f)

    except json.decoder.JSONDecodeError:
        with open(fileName, 'w+') as f:
            json.dump(data, f)


client = None

def _initializeEtcd():
    global client
    client = etcd.Client(host='127.0.0.1', port=2379)
    return client

def storeContainer(appName, containerID):
    client = _initializeEtcd()
    client.write('/app/'+appName, containerID, append=True)

def getContainers(appName):
    client = _initializeEtcd()
    dir = client.get('/app/'+appName)
    return dir.children

if __name__=="__main__":
    print("something")

    #     client = storeContainer('abc', '1234')
    #
    #
    #     children = getContainers('abc')
    #     print(list(map( lambda x: x.value, children)))