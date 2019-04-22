A simple cloud (cluster of docker containers) management tool written in python. It provides, manual scaling, auto scaling and fault-tolerance.

### Steps
1. make sure you create a python3 virtualenv and activate it 
1. do pip install -r requirements
2. run python SimpleCluster/Manager.py
3. make sure you have a local etcd server running on port 2379,
if its running on a different port, set it in the SimpleCluster/StateStorage.py file


### Commands
1. help, will list all the commands available
2. ps, will list all of the apps that are running
3. start <app-name>, will start a new app
4. list <app-name>, will list the containers for that app
5. stop <app-name>, will stop the app
6. scaleup <app-name> <number-of-workers>, will scale the app to the specified number
7. scaledown <app-name> <number-of-workers>, will scale down the app to the specified number
8. start-autoscaling <app-name> will start autoscaling 
9. stop-autoscaling <app-name> will stop autoscaling
10. if anything goes wrong there is a "clean-slate" command that will remove everything



### Parallel Threads
We have two parallel threads running apart from the main one
1. auto-scaling thread, that is started or stop with the autoscaling command
2. house-cleaning thread, this is started as soon as the manager starts. This monitors the number of workers that should be running for a particular application. This threa is responsible for respawning dead workers. The check is made every 10 secs.
