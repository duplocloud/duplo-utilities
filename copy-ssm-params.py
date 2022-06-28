import os
import json
import logging
import requests
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


class DuploConfig:
    def __init__(self, src_duplo_host, src_duplo_token, src_tenant_id, dest_duplo_host, dest_duplo_token, dest_tenant_id):
        self.src_duplo_host = src_duplo_host
        self.src_duplo_token = src_duplo_token
        self.src_tenant_id = src_tenant_id
        self.dest_tenant_id = dest_tenant_id
        self.dest_duplo_host = dest_duplo_host
        self.dest_duplo_token = dest_duplo_token


def main():
    check_env_var_present(
        'src_duplo_host', "Environment variable 'src_duplo_host' not found.")
    src_duplo_host = os.environ['src_duplo_host']
    check_env_var_present(
        'src_duplo_token', "Environment variable 'src_duplo_token' not found.")
    src_duplo_token = os.environ['src_duplo_token']
    check_env_var_present(
        'src_tenant_id', "Environment variable 'src_tenant_id' not found.")
    src_tenant_id = os.environ['src_tenant_id']
    check_env_var_present(
        'dest_duplo_host', "Environment variable 'dest_duplo_host' not found.")
    dest_duplo_host = os.environ['dest_duplo_host']
    check_env_var_present(
        'dest_duplo_token', "Environment variable 'dest_duplo_token' not found.")
    dest_duplo_token = os.environ['dest_duplo_token']
    check_env_var_present(
        'dest_tenant_id', "Environment variable 'dest_tenant_id' not found.")
    dest_tenant_id = os.environ['dest_tenant_id']
    duplo_config = DuploConfig(
        src_duplo_host, src_duplo_token, src_tenant_id, dest_duplo_host, dest_duplo_token, dest_tenant_id)
    ssm_params = list_duplo_ssm_params(duplo_config)
    if len(ssm_params) == 0:
        logging.info(
            "SSM params not found in source tenant %s.", src_tenant_id)
        return
    logging.info(ssm_params)
    for ssm_param in ssm_params:
        create_duplo_ssm_param(
            duplo_config, view_duplo_ssm_param(duplo_config, ssm_param['Name']))


def list_duplo_ssm_params(duplo_config):
    list_duplo_ssm_params_url = "/".join((duplo_config.src_duplo_host,
                                          "v3/subscriptions", duplo_config.src_tenant_id, "aws/ssmParameter"))
    logging.info("list_duplo_ssm_params_url(%s)", list_duplo_ssm_params_url)
    headers = {
        'Authorization': 'Bearer ' + duplo_config.src_duplo_token,
        'Content-Type': 'application/json'
    }
    payload = {}
    try:
        response = requests.request(
            "GET", list_duplo_ssm_params_url, headers=headers, data=payload)
        response.raise_for_status()

        json_response = json.loads(response.text)

        logging.debug(
            "API - %s, Response - %s", list_duplo_ssm_params_url, json_response)
        return json_response
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        # print(e, file=sys.stderr)
        raise SystemExit(e)


def create_duplo_ssm_param(duplo_config, src_ssm_param):
    logging.info("Creating ssm param --> '%s'.", src_ssm_param['Name'])
    url = "/".join((duplo_config.dest_duplo_host,
                    "v3/subscriptions", duplo_config.dest_tenant_id, "aws/ssmParameter"))
    payload = json.dumps({
        "Name": src_ssm_param['Name'],
        "Type": src_ssm_param['Type'],
        "Value": src_ssm_param['Value'],
        "Description": src_ssm_param['Description'],
    })
    headers = {
        'Authorization': 'Bearer ' + duplo_config.dest_duplo_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request(
            "POST", url, headers=headers, data=payload)
        response.raise_for_status()
        logging.info("SSM param (%s) created successfully.",
                     src_ssm_param['Name'])
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def view_duplo_ssm_param(duplo_config, param_name):
    view_duplo_ssm_param_url = "/".join((duplo_config.src_duplo_host,
                                         "v3/subscriptions", duplo_config.src_tenant_id, "aws/ssmParameter", param_name))
    logging.info("view_duplo_ssm_param(%s)", view_duplo_ssm_param_url)
    headers = {
        'Authorization': 'Bearer ' + duplo_config.src_duplo_token,
        'Content-Type': 'application/json'
    }
    payload = {}
    try:
        response = requests.request(
            "GET", view_duplo_ssm_param_url, headers=headers, data=payload)
        response.raise_for_status()

        json_response = json.loads(response.text)

        logging.debug(
            "API - %s, Response - %s", view_duplo_ssm_param_url, json_response)
        return json_response
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        # print(e, file=sys.stderr)
        raise SystemExit(e)


def check_env_var_present(env_key, err_msg):
    try:
        os.environ[env_key]
    except KeyError:
        raise KeyError(err_msg)


if __name__ == "__main__":
    main()
