    import boto3
    import gzip

    s3 = boto3.client('s3')

    def get_file(event, bucket, key):
        response = s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()


    def lambda_handler(event, context):
        destBucketName = 'agwa-logs-compressed'
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        # gettinf uploaded file
        fileContent = get_file(event, bucket, key)

        # comppressing file
        fileCompressed = gzip.compress(fileContent)
        keyCompressedFile = "{}.gz".format(key)
        
        # uploading compressed file
        s3.put_object(Bucket=destBucketName, Key=keyCompressedFile, Body=fileCompressed)
