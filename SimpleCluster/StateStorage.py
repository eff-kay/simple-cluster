import json
import os

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




if __name__=="__main__":
    print("something")