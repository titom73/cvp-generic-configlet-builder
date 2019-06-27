import yaml
import os
import json
from jinja2 import Template, Environment, FileSystemLoader
### Specific CVP Libraries
from cvplibrary import CVPGlobalVariables, GlobalVariableNames 
from cvplibrary import RestClient 
import requests
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

"""
Generic configlet builder for Jinj2 rendering with JSON
"""

__author__ = "Thomas Grimonet"
__license__ = "GPL"
__version__ = "0.0.1"
__date__ = "27/06/2019"
__maintainer__ = "Thomas Grimonet"

# Configlet name where to get the JINJA2 template
TEMPLATE_FILE = '10-TEMPLATE-LEAF'
# Configlet name where to get data related device
HOST_DATA_FILE = '10-DATA-'
# Additionnal configlet with JSON content to load data
GLOBAL_DATA_FILE = []
# CVP IP address to connect to. 
# Should not be changed unless you know what to do.
CVP_ADDRESS='127.0.0.1'

def cvp_query(postfix, http_type='GET', data=None):
    """
    Function to query CVP API engine.
    
    Parameters
    ----------
    postfix : str
        URI to query on CVP
    http_type : str, optional
        HTTP method to interact with API, by default 'GET'
    data : [type], optional
        Data to send in case of a PUT/POST method, by default None
    
    Returns
    -------
    dcit
        server response.
    """
    response = False
    query_string = 'https://{0}/cvpservice/{1}'.format(CVP_ADDRESS, postfix)
    client = RestClient(query_string, http_type)
    if http_type == 'POST':
        client.setRawData(json.dumps(data))
    if client.connect():
        response = json.loads(client.getResponse())
    return response


def configlet_get(configlet_name):
    """
   get content of a configlet from CVP.
    
    Parameters
    ----------
    configlet_name : str
        Name of configlet to get from CVP
    
    Returns
    -------
    str
       Content of the configlet only 
    """
    response_data = cvp_query('configlet/getConfigletByName.do?name={0}'.format(configlet_name))['config']
    return response_data


def json_merge(json1, json2):
    """
    Function to merge 2 JSON.
    
    Parameters
    ----------
    json1 : json
        First JSON to merge
    json2 : json
        Second Json to merge
    
    Returns
    -------
    json
        Merged json.
    """
    json_merged = {k: v for d in [json1, json2] for k, v in d.items()}
    return json_merged


def hostname_get(deviceIP):
    """
    Get device hostname from CVP from a managment IP
    
    Parameters
    ----------
    deviceIP : str
        Managment IP of device to look for hostname.
    
    Returns
    -------
    str
        device hostname if found, else return None
    """
    device_list = cvp_query('inventory/devices')
    for device in device_list:
        if deviceIP == device['ipAddress']:
            return device['fqdn']
    return None


if __name__ == '__main__':

    # get hostname for a given management IP
    device_mgtIp =CVPGlobalVariables.getValue( GlobalVariableNames.CVP_IP )
    device_hostname = hostname_get(device_mgtIp)

    # Load content from configlets.
    device_data_configlet = '{0}{1}'.format(HOST_DATA_FILE,device_hostname)
    data = json.loads(configlet_get(device_data_configlet))
    template_content = configlet_get(TEMPLATE_FILE)

    for data_configlet in GLOBAL_DATA_FILE:
        data_json = json.loads(configlet_get(data_configlet))
        data = json_merge(data, data_json)

    template = Template(template_content)
    
    # Save output
    print template.render(data)
