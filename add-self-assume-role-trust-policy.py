import boto3
import json
import sys

if __name__ == '__main__':
    session = boto3.session.Session(profile_name = sys.argv[1])
    client = session.client('iam')

    iamRoleName = 'duplomaster'

    if len(sys.argv) > 2:
       iamRoleName =  sys.argv[2]

    response = client.get_role(
        RoleName = iamRoleName
    )
    print("Duplo master role arn - " + response['Role']["Arn"])
    trustDocument = response['Role']["AssumeRolePolicyDocument"]

    duploTrustPolicy = {
        "Sid": "DuploMasterSelfAssume",
        "Effect": "Allow",
        "Principal": {
            "AWS": response['Role']["Arn"]
        },
        "Action": [
            "sts:AssumeRole",
            "sts:TagSession"
        ]
    }

    found = False
    for statement in trustDocument["Statement"]:
        if "Sid" in statement and statement["Sid"] == "DuploMasterSelfAssume":
            found = True
            break
    
    if not found:
        print("Self Assume Policy not found going to add it")
        trustDocument["Statement"].append(duploTrustPolicy)

        updateResponse = client.update_assume_role_policy(
            PolicyDocument= json.dumps(trustDocument),
            RoleName = iamRoleName,
        )
        print("Policy update complete, see response below")
        print(updateResponse)
    else:
        print("Policy already found no need to update")
