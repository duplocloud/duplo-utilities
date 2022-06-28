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
    secrets = list_duplo_aws_secrets(duplo_config)
    logging.info(secrets)
    src_tenant_name = get_tenant_name_by_id(duplo_config)
    for secret in secrets:
        secret_data = view_duplo_aws_secret(duplo_config, secret['Name'])
        logging.info("Creating duplo AWS secret %s for tenant - %s",
                     secret['Name'], src_tenant_name)
        # print("=============================================")
        # print(secret)
        secret_short_name = secret['Name'][len(
            "duploservices--") + len(src_tenant_name):len(secret['Name'])]
        print("Secret Short Name --> %s" % secret_short_name)
        create_duplo_aws_secret(duplo_config, secret_short_name, secret_data)


def list_duplo_aws_secrets(duplo_config):
    list_duplo_aws_secrets_url = "/".join((duplo_config.src_duplo_host,
                                           "subscriptions", duplo_config.src_tenant_id, "ListTenantSecrets"))
    logging.info("list_duplo_aws_secrets(%s)", list_duplo_aws_secrets_url)
    headers = {
        'Authorization': 'Bearer ' + duplo_config.src_duplo_token,
        'Content-Type': 'application/json'
    }
    payload = {}
    try:
        response = requests.request(
            "GET", list_duplo_aws_secrets_url, headers=headers, data=payload)
        response.raise_for_status()

        json_response = json.loads(response.text)

        logging.debug(
            "API - %s, Response - %s", list_duplo_aws_secrets_url, json_response)
        return json_response
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        # print(e, file=sys.stderr)
        raise SystemExit(e)


def create_duplo_aws_secret(duplo_config, secret_name, secret_string):
    logging.info("Creating secret --> '%s'.", secret_name)
    url = "/".join((duplo_config.dest_duplo_host,
                    "subscriptions", duplo_config.dest_tenant_id, "CreateTenantSecret"))
    payload = json.dumps({
        "Name": secret_name,
        "SecretString": secret_string,
    })
    headers = {
        'Authorization': 'Bearer ' + duplo_config.dest_duplo_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request(
            "POST", url, headers=headers, data=payload)
        response.raise_for_status()
        logging.info("Secrets (%s) created successfully.", secret_name)
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def get_tenant_name_by_id(duplo_config):
    get_tenant_name_by_id_url = "/".join((duplo_config.src_duplo_host,
                                          "v2/admin/TenantV2", duplo_config.src_tenant_id))
    logging.info("get_tenant_name_by_id(%s)", get_tenant_name_by_id_url)
    headers = {
        'Authorization': 'Bearer ' + duplo_config.src_duplo_token,
        'Content-Type': 'application/json'
    }
    payload = {}
    try:
        response = requests.request(
            "GET", get_tenant_name_by_id_url, headers=headers, data=payload)
        response.raise_for_status()

        json_response = json.loads(response.text)

        logging.debug(
            "API - %s, Response - %s", get_tenant_name_by_id_url, json_response)
        return json_response['AccountName']
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        # print(e, file=sys.stderr)
        raise SystemExit(e)


def view_duplo_aws_secret(duplo_config, secret_name):
    view_duplo_aws_secret_url = "/".join((duplo_config.src_duplo_host,
                                          "v3/subscriptions", duplo_config.src_tenant_id, "aws/secret", secret_name))
    logging.info("view_duplo_aws_secret(%s)", view_duplo_aws_secret_url)
    headers = {
        'Authorization': 'Bearer ' + duplo_config.src_duplo_token,
        'Content-Type': 'application/json'
    }
    payload = {}
    try:
        response = requests.request(
            "GET", view_duplo_aws_secret_url, headers=headers, data=payload)
        response.raise_for_status()

        json_response = json.loads(response.text)

        logging.debug(
            "API - %s, Response - %s", view_duplo_aws_secret_url, json_response)
        return json_response['SecretString']
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
