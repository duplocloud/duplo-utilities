import os
import json
import requests;
from unicodedata import name
import time

logLevel="info"
tenantName="dev01";
tenantId="b39a883e-0577-4dfc-9c51-dd5e42c1f67a";
duploHost="https://azibo.duplocloud.net/"
duploToken="AQAAANCMnd8BFdERjHoAwE_Cl-sBAAAATIeXUjCrgUS3N8IoiC2ENQAAAAACAAAAAAAQZgAAAAEAACAAAAD92whNSsCRmdO0Ru_lg6QgWViLdbi7-bWSmF2afzfqsQAAAAAOgAAAAAIAACAAAAC4xYb0PLPWjxdtr4tfkiFb5n78ckWXdFbLwwdvn17b6pAAAAAqpELEaluFtfvr2YanPth1tOFXFx2_dUcC0iDKz0NTAjRsvoZoOWsaf7bvVTI5SVDVRNGixkvGel0y1KCZoa3rEloZcxTGNppNHMMP1CTIIcMVTZ1Og3TBgH9FfLPcSW6t3rrGdBTG03GTbkuOKlkPDS5dG4pLQLMuTKTF0ZxJ7U4iY2ZGlhy8AVlFT7SKFg1AAAAAWipCTRVLHdsvmnOoaYb-Rbl0Z2QATrfHKVfYY4PIeij25u7rMdnd_ziIaAaX6JLWCxAMPlNE93YGmpnCZnDeyQ"
def info(line):
    if logLevel == 'info' or logLevel=='debug':
        print(f"Info: {line}");
def debug(line):
    if logLevel=='debug':
        print(f"Debug: {line}");

def getHeaders():
    headers = {'Authorization': 'Bearer ' + duploToken};
    return headers;

def duploGet(url):
    info(f"Get request url: {url}")
    response = requests.get(f'{duploHost}/{url}', headers=getHeaders())
    info(f"Get response url: {url},  response: {response}")
    return json.loads(response.text)

def duploPost(url, req):
    info(f"Post request url: {url}")
    response = requests.post(f'{duploHost}/{url}', headers=getHeaders(), json=req)
    info(f"Post request url: {url},  response: {response}")
    return json.loads(response.text)

def deleteRC(rc):
    info(f"Delete RC {rc['Name']}")
    rc["State"] = "delete"
    # req = {
    #     "TenantId":tenantId,
    #     "State":"delete",
    #     "Name":rc["Name"],
    #     "NetworkId":"default",
    #     "DockerImage":rc["Image"],
    #     "AgentPlatform":7
    # }
    url = f"subscriptions/{tenantId}/ReplicationControllerUpdate"
    duploPost(url, rc)

def postDuploService(rc, update):
    url = f"subscriptions/{tenantId}/ReplicationControllerUpdate"
    duploPost(url, rc)

def getDuploService(name):
    url = f'subscriptions/{tenantId}/GetReplicationControllers'
    rcs = duploGet(url);
    for rc in rcs:
        if rc['Name'] == name:
            return rc;
    return None

def createLB(name, taskDef, update):
    cd = taskDef['containerDefinitions'][0];
    if cd['portMappings']:
        for portMapping in cd["portMappings"]:
            lb = {   
                "HealthCheckConfig":{},
                "LbType":3,
                "Port":portMapping["containerPort"],
                "ExternalPort":portMapping["hostPort"],
                "Protocol":portMapping["protocol"],
                "ReplicationControllerName": name,
                "ExtraSelectorLabels":[]
            }
            if cd["healthCheck"]:
                lb["HealthCheckUrl"] = cd["healthCheck"]
            else:
                lb["HealthCheckUrl"] = "/"
            duploPost(f"subscriptions/{tenantId}/LBConfigurationUpdate", lb)
def createRC(name, taskDef, update):
    rc = {};
    cd = taskDef['containerDefinitions'][0];
    rc['DockerImage'] = cd['image']
    rc['Name'] = name
    rc["Replicas"] = 1;
    rc["TenantId"] = tenantId;
    rc["NetworkId"] = "default";
    rc["IsDaemonset"] = 0;
    rc["Cloud"] = 0;
    rc["AgentPlatform"] = 7;
    rc["AllocationTags"] = "app";
    envs = cd['environment']
    otherDockerConfigs = {};
    if envs:
        newEnvs = []
        for env in envs:
            newEnvs.append({"Name": env['name'], "Value": env['value']})
        otherDockerConfigs["Env"] = newEnvs;
   
    if taskDef['memory'] or taskDef['cpu']:
        resources = {
            "Limits": {
            },
            "Requests": {
            }
        }
        if taskDef['memory'] :
            mem = int(taskDef['memory']);
            resources["Limits"]["memory"] = f"{mem}Mi";
            resources["Requests"]["memory"] = f"{int( mem / 2)}Mi";
        if taskDef['cpu'] :
            cpu = int(taskDef['cpu']);
            resources["Limits"]["cpu"] = f"{cpu}m";
            resources["Requests"]["cpu"] = f"{int(cpu / 2)}m";

        otherDockerConfigs["Resources"] = resources;
    rc["OtherDockerConfig"] = json.dumps(otherDockerConfigs);
    info(f"Save Replication Controller: {json.dumps(rc)}");
    postDuploService(rc, update);
def inportToDuplo(file):
    print(f"Import file: {file}")
    f = open(f"ecs-tasks/{file}")
    taskDef = json.load(f);
    taskDefName=taskDef['family'];
    taskDefName = taskDefName.replace("staging-", "")
    taskDefName = taskDefName.replace("-staging", "")
    taskDefName = taskDefName.replace("-staging", "")
    print(f"Import task Definition: {taskDefName}")
    rc = getDuploService(taskDefName)
    update =  rc != None;
    info(f"IsUpdate: {update}")
    if update:
        deleteRC(rc)
    
    time.sleep(2)

    createRC(taskDefName, taskDef, update)
    createLB(taskDefName, taskDef, update)

    print("")
    print("")


for filename in os.listdir("ecs-tasks"):
  inportToDuplo(filename);