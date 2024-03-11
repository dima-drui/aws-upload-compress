    import base64
    import boto3
    import re
    import hashlib

    s3 = boto3.client('s3')

    def get_file_name(header):
        file_name_get = header['Content-Disposition']
        file_name = re.search(r'\"(.*?)\"', file_name_get).group(1)
        return file_name

    def is_file_exist(bucket, file_key):
        try:
            content = s3.head_object(Bucket=bucket, Key=file_key)
            if content.get('ResponseMetadata',None) is not None:
                raise Exception(f"File with the name {file_key} already exists")
        except Exception as a:
            for arg in a.args:
                # if file not found - continue 
                if arg == 'An error occurred (404) when calling the HeadObject operation: Not Found':
                    return
            raise a

    def lambda_handler(event, context):
        bucket_name = 'agwa-logs-original'

        # getting file name
        file_name = get_file_name(event['params']['header'])

        # check file not exists
        is_file_exist(bucket_name, file_name)

        # uploading file
        # md5 allows to control sucssesfull uploading
        content_get = event['content']
        content_decoded = base64.b64decode(content_get)
        md5_hash = hashlib.md5(content_decoded).digest()
        md5_result = base64.b64encode(md5_hash).decode('utf-8')
        res = s3.put_object(Bucket=bucket_name, Key=file_name, Body=content_decoded, ContentMD5=md5_result)
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {
                "statusCode": 200,
                "body": 'Object is Uploaded successfully!'
            }
        else:
            return {
                "statusCode": 400,
                "body": f'The {file_name} was not uploaded, try again'
            }
