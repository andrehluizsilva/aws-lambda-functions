var AWS = require('aws-sdk');

exports.handler = function(event, context) {
    var ec2 = new AWS.EC2({region: 'us-west-1'});
    ec2.stopInstances({InstanceIds : ['i-3135ae6b', 'i-d035158b', 'i-064fcb5fc047f13e7'] },function (err, data) {
        if (err) 
            console.log(err, err.stack); // an error occurred
        else 
            console.log(data); // successful response

        context.done(err,data);
    });

    var rds = new AWS.RDS({region: 'us-west-1'});
    rds.stopDBInstance({DBInstanceIdentifier: 'imx-db-pre-prod-web-sql-server'}, function (err, data) {
        if (err)
            console.log(err, err.stack); // an error occurred  
        else
            console.log(data); // successful response
    });
};