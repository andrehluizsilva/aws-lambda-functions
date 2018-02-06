import boto3
import datetime

ec = boto3.client('ec2')

def lambda_handler(event, context):
    reservations = ec.describe_instances(
            Filters=[{'Name': 'tag-key', 'Values': ['AutoBackup']},]
        ).get('Reservations', [])

    instances = sum([[i for i in r['Instances']] for r in reservations], [])

    print "Found %d instances that need backing up" % len(instances)

    for instance in instances:
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Retention'][0]
        except IndexError:
            retention_days = 30
            
        try:
            instance_name = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Name'][0]
        except IndexError:
            instance_name = instance['InstanceId']

        create_time = datetime.datetime.now()
        create_fmt = create_time.strftime('%Y-%m-%d')

        AMIid = ec.create_image(
            InstanceId=instance['InstanceId'],
            Name="Auto Backup - " + instance_name ,
            Description="Auto Backup created AMI of instance " + instance_name + " on " + create_fmt,
            NoReboot=True,
            DryRun=False)

        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%Y-%m-%d')
        ec.create_tags(DryRun=False, Resources=[AMIid['ImageId'],],
            Tags=[
                { 'Key': 'DeleteOn', 'Value': delete_fmt },
                { 'Key': 'instance-id', 'Value':instance['InstanceId'] },
                { 'Key': 'instance-type', 'Value':instance['InstanceType'] }
            ])
        ec.create_tags(DryRun=False, Resources=[AMIid['ImageId'],], Tags=instance['Tags']) 

        image = ec.describe_images(
            DryRun=False,
            ImageIds=[
                AMIid['ImageId'],
            ],
        )

        blocks = image['BlockDeviceMappings']
        for bd in blocks:
            ec.create_tags(DryRun=False, Resources=[bd['Ebs']['SnapshotId'],], Tags=instance['Tags']) 

        print "Retaining AMI %s of instance %s for %d days" % (
            AMIid['ImageId'],
            instance['InstanceId'],
            retention_days,
        )