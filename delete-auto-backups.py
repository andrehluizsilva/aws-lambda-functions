import boto3
import datetime

ec = boto3.client('ec2')

def lambda_handler(event, context):
    delete_time = datetime.datetime.now()
    delete_fmt = delete_time.strftime('%Y-%m-%d')

    ecResponse = ec.describe_images(
        DryRun=False,
        Filters=[
            {
                'Name': 'tag:DeleteOn',
                'Values': [
                    delete_fmt
                ]
            },
        ]
    )
    
    print 'Images found: ' + str(len(ecResponse['Images']))

    for image in ecResponse['Images']:
        print 'Deregistering ' + image['ImageId']
        ec.deregister_image(
            DryRun=False,
            ImageId=image['ImageId']
        )
        blocks = image['BlockDeviceMappings']
        for bd in blocks:
            ec.delete_snapshot(
                DryRun=False,
                SnapshotId=bd['Ebs']['SnapshotId']
            )
