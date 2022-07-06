import requests
import json
import os
import subprocess
import requests
from requests.structures import CaseInsensitiveDict
import yaml
import time
import sys
import urllib3
from collections import OrderedDict
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
import re
from jinja2 import Environment, FileSystemLoader
import ast
import sys
import ruamel.yaml
import yaml

def listToString(s):
    str1 = " "
    return (str1.join(s))

host = ['10.3.0.6', '10.3.0.4']

def ingress_ha_job():
    for hostname in host:
        url = "https://"+hostname+"/api/user/login"
        payload = json.dumps({   #can also use API key for API requests
          "username": "admin",
          "password": "password"
        })
        headers = {
          'Content-Type': 'application/json'
        }
        session = requests.session()
        try:
            response = session.post(url, headers=headers, data=payload, verify=False, timeout=5)
        except:
            continue
        res = response.json()
        code = response.status_code
        token = res['token']
        t2 = str(token)
        last_time = response.cookies.get_dict()
        hastatus_url = "https://"+hostname+"/api/system_ha/brief_status"

        headers = CaseInsensitiveDict()
        headers["cookie"] = "last_access_time="+listToString(last_time.values())
        headers["Authorization"] = "Bearer "+token


        resp2 = requests.get(hastatus_url, headers=headers, verify=False)

        res2 = resp2.json()

        if (res2['payload']['local_state']) == "VRRP (Working)":
                file_in = open("simple-fanout-example.yaml", "r")
                yaml = ruamel.yaml.YAML()
                yaml.preserve_quotes = True
                yaml.width = 1024
                data = yaml.load(file_in)
                ip = data["metadata"]["annotations"]["fortiadc-ip"]
                annotations = data["metadata"]["annotations"]

                for k,v in annotations.items():
                    if k == 'fortiadc-ip':
                        if ip == hostname:
                            exit()
                        if ip != hostname:
                            delete_url = "https://"+hostname+"/api/load_balance_virtual_server?mkey=fortiadc-ingress_simple-fanout-example"
                            delete = requests.delete(delete_url, headers=headers, verify=False)
                            write_to_yaml(hostname)

def write_to_yaml(hostname):

    file_in = open("simple-fanout-example.yaml", "r")
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.width = 1024
    data = yaml.load(file_in)
    annotations = data['metadata']['annotations']
    annotations['fortiadc-ip'] = type(annotations['fortiadc-ip'])(hostname)
    annotations['virtual-server-ip'] = type(annotations['virtual-server-ip'])(hostname)
    sys.stdout = open('simple-fanout-example.yaml', 'w')
    yaml.dump(data, sys.stdout)


command = 'kubectl apply -f simple-fanout-example.yaml -n fortiadc-ingress'
os.system(command)




ingress_ha_job()
