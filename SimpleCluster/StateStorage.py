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
        if w.key != '/apps/' + appName + '/lb' and w.key != '/apps/' + appName + '/lbport':
            workerIds.append(w.value)
    return workerIds


def saveLbState(appName, lbId, port):
    client.write('/apps/' + appName + '/lb', lbId)
    client.write('/apps/' + appName + '/lbport', port)


def getLBPortForApp(appName):
    lbId = None
    try:
        numWorkers = client.get('/apps/' + appName)
    except:
        return None

    for w in numWorkers.children:
        if w.key != '/apps/' + appName + '/lbport':
            pass
        else:
            lbId = w.value
    return lbId

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
        client.delete('/apps/' + appName + '/lbport')
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

def getTotalApps():
    running_apps = []
    try:
        runningApps = client.get('/apps')
    except:
        return None

    if runningApps._children is not None:
        for app in runningApps._children:
            running_apps.append(app['key'].split("/")[2])
    return running_apps

if __name__=="__main__":
    print("something")

    #     client = storeContainer('abc', '1234')
    #
    #
    #     children = getContainers('abc')
    #     print(list(map( lambda x: x.value, children)))