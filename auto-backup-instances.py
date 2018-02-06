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
        create_time = datetime.datetime.now()
        create_fmt = create_time.strftime('%Y-%m-%d')

        AMIid = ec.create_image(InstanceId=instance['InstanceId'],
            Name="Auto Backup - " + instance['InstanceId'] + " from " + create_fmt,
            Description="Auto Backup created AMI of instance " + instance['InstanceId'],
            NoReboot=True,
            DryRun=False)

        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%Y-%m-%d')
        ec.create_tags(DryRun=False, Resources=[AMIid['ImageId'],],
            Tags=[
                {
                    'Key': 'DeleteOn',
                    'Value': delete_fmt
                },
            ])

        print "Retaining AMI %s of instance %s for %d days" % (
            AMIid['ImageId'],
            instance['InstanceId'],
            retention_days,
        )