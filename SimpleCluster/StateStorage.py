# client = None
#
# def _initializeEtcd():
#     global client
#     client = etcd.Client(host='127.0.0.1', port=2379)
#     return client
#
# def storeContainer(appName, containerID):
#     client = _initializeEtcd()
#     client.write('/app/'+appName, containerID, append=True)
#
# def getContainers(appName):
#     client = _initializeEtcd()
#     dir = client.get('/app/'+appName)
#     return dir.children


import etcd

client = etcd.Client(port=2379)


def saveAppState(appName, id):
    client.write('/apps/' + appName, id, append=True)


def getWorkersForApp(appName):
    workerIds = []
    try:
        numWorkers = client.get('/apps/' + appName)
    except:
        return None

    for w in numWorkers.children:
        if w.key != '/apps/' + appName + '/lb':
            workerIds.append(w.value)
    return workerIds


def saveLbState(appName, lbId):
    client.write('/apps/' + appName + '/lb', lbId)


def getLbForApp(appName):
    lbId = None
    try:
        numWorkers = client.get('/apps/' + appName)
    except:
        return None

    for w in numWorkers.children:
        if w.key != '/apps/' + appName + '/lb':
            pass
        else:
            lbId = w.value
    return lbId


def deleteAppState(appName):
    try:
        client.delete('/apps/' + appName, recursive=True)
        return True
    except:
        return None


def deleteLbState(appName):
    try:
        client.delete('/apps/' + appName + '/lb')
        return True
    except:
        return None


def deleteWorkerforApp(appName, workerId):
    keyFound = False
    try:
        numWorkers = client.get('/apps/' + appName)
    except:
        return None

    for w in numWorkers.children:
        if w.value == workerId:
            client.delete(w.key)
            keyFound = True

    return keyFound


def getCpuUsageFromEtcd(worker):
    if worker in client:
        return client.get(worker).value
    else:
        return 0


def setCpuUsageFromEtcd(worker, val):
    client.write(worker, val)

if __name__=="__main__":
    print("something")

    #     client = storeContainer('abc', '1234')
    #
    #
    #     children = getContainers('abc')
    #     print(list(map( lambda x: x.value, children)))