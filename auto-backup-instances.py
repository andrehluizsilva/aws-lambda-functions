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
                t.get('Value') for t in instance['Tags']
                if t['Key'] == 'Name'][0]
        except IndexError:
            instance_name = instance['InstanceId']

        create_time = datetime.datetime.now()
        create_fmt = create_time.strftime('%Y-%m-%d %H-%M-%S')
        
        AMIName = "Auto Backup [" + create_fmt + "] - " + instance_name 
        AMIDescription = "Auto Backup created AMI of instance " + instance_name + " (" + instance['InstanceId']  + ") on " + create_fmt

        print "AMI Name: %s" % AMIName
        print "AMI Description: %s" % AMIDescription

        AMIid = ec.create_image(
            InstanceId=instance['InstanceId'],
            Name= AMIName,
            Description=AMIDescription,
            NoReboot=True,
            DryRun=False)

        print "Created image for instance: %s on %s" % (
            instance_name,
            create_fmt,
        )
        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%Y-%m-%d')

        tags = [
                { 'Key': 'DeleteOn', 'Value': delete_fmt },
                { 'Key': 'instance-id', 'Value':instance['InstanceId'] },
                { 'Key': 'instance-type', 'Value':instance['InstanceType'] }
               ] + instance['Tags']

        aws_tags = []
        for tag in tags:
            aws_tags.extend([ tag for k,v in tag.items() if 'aws:' in v])
        for k in aws_tags:
            tags.remove(k)
        
        ec.create_tags(DryRun=False, Resources=[AMIid['ImageId'],], Tags=tags)
        
        print "Created tags for image: %s" % (
            AMIid['ImageId'],
        )
        
        print "Retaining AMI %s of instance %s for %d days" % (
            AMIid['ImageId'],
            instance_name,
            retention_days,
        )