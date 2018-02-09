import json
import boto3
import time
import datetime

def lambda_handler(event, context):
    #print('Received event: ' + json.dumps(event, indent=2))
    #print(event)
    #rint(context)

    ids = []

    try:
        region = event['region']
        detail = event['detail']
        eventname = detail['eventName']
        arn = detail['userIdentity']['arn']
        principal = detail['userIdentity']['principalId']
        userType = detail['userIdentity']['type']

        if userType == 'IAMUser':
            user = detail['userIdentity']['userName']
        else:
            user = principal.split(':')[1]

        print "INFO: principalId: %s" % str(principal)
        print "INFO: region: %s" % str(region)
        print "INFO: eventName: %s" % str(eventname)
        #print "INFO: detail: %s" % str(detail)

        if not detail['responseElements']:
            print "WARNING: Not responseElements found"
            if detail['errorCode']:
                print "ERROR: errorCode: %s" % detail['errorCode']
            if detail['errorMessage']:
                print "ERROR: errorMessage: %s" % detail['errorMessage']
            return False

        ec2 = boto3.resource('ec2')
        ec = boto3.client('ec2')

        if eventname == 'CreateVolume':
            ids.append(detail['responseElements']['volumeId'])
            print "INFO: volume-id: %s" % detail['responseElements']['volumeId']

        elif eventname == 'RunInstances':
            items = detail['responseElements']['instancesSet']['items']
            for item in items:
                ids.append(item['instanceId'])
                print "INFO: instance-id: %s" % item['instanceId']
            print "INFO: number of instances: %s" % str(len(ids))

            base = ec2.instances.filter(InstanceIds=ids)

            #loop through the instances
            for instance in base:
                for vol in instance.volumes.all():
                    ids.append(vol.id)
                for eni in instance.network_interfaces:
                    ids.append(eni.id)

        elif eventname == 'CreateImage':
            ids.append(detail['responseElements']['imageId'])
            image = ec2.Image(detail['responseElements']['imageId'])
            print "INFO: Image id: %s - status: %s" % (image.image_id, image.state)
            
            blocks = image.block_device_mappings
            for bd in blocks:
                ids.append(bd['Ebs']['SnapshotId'])
                print "INFO: snapshot-id: %s" %bd['Ebs']['SnapshotId']
                ec.create_tags(DryRun=False, Resources=[bd['Ebs']['SnapshotId'],], Tags=image.tags) 
                print "Created tags for snapshot: %s" % (
                    bd['Ebs']['SnapshotId'],
                )

        elif eventname == 'CreateSnapshot':
            ids.append(detail['responseElements']['snapshotId'])
            print "INFO: snapshot-id: %s" % detail['responseElements']['snapshotId']
        else:
            print "WARNING: Not supported action"

        if ids:
            for resourceid in ids:
                print "Tagging resource %s" % resourceid
            ec2.create_tags(Resources=ids, Tags=[{'Key': 'Owner', 'Value': user}, {'Key': 'PrincipalId', 'Value': principal}])

        print "INFO: Remaining time (ms): %s \\n" % str(context.get_remaining_time_in_millis())
        return True
    except Exception as e:
        print "ERROR: Something went wrong: %s" % str(e)
        return False