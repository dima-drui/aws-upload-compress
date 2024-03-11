
# Log File Upload and Auto-Compression System

Assignment Goal: Design and implement a solution to enable log file upload and auto-comperssion.





# Components


- #### **Gateway** - POST: /logs
Accepts requests with a file, checks endpoint access permissions using IAM and prepares headers

- #### **Lambda 1** - agwa-Logs-ApiToS3
Validates the request header and content.
Saves the file to the S3 bucket 1.
Returns a success response or an error message with the stage at which the error occurred.

- #### **Lambda 2** - agwa-Logs-S3ComppressS3
Triggered by a "PUT" event in the S3 bucket 1.
Compresses the file using gzip.
Uploads the compressed file to the S3 bucket 2.

- #### **S3 Bucket 1** - agwa-logs-original
Stores the original files uploaded through the API Gateway.

- #### **S3 Bucket 2** - agwa-logs-compressed
Stores the compressed files
# Deployment


### 1. AWS GATEWAY
- Navigate to "API Gateway" > "APIs"
- Create a new API 
- Create a new Resource '/logs'
- Create a new Method 'POST'
- Click "Edit" on the "Integration request" of the method tab. Add "mapping template":

Content type: text/plain

Template body:
```html
    #set($allParams = $input.params())

    {
    "params" : {
        #foreach($type in $allParams.keySet())
        #set($params = $allParams.get($type))
        "$type" : {
        #foreach($paramName in $params.keySet())
        "$paramName" : "$util.escapeJavaScript($params.get($paramName))"
        #if($foreach.hasNext),#end
        #end
        }
        #if($foreach.hasNext),#end
        #end
    },
    "content": "$input.body"
    }
```

- Click "Save"
- Click "API settings" in the sidebar
- Click "Manage media types" and add type: "text/plain"

### 2. AWS S3 BUCKETS
- Navigate to "Amazon S3" > "Buckets"
- Click "Create bucket". Enter name: "agwa-logs-original", click "Create bucket".
- Click "Create bucket" again. Enter name: "agwa-logs-compressed", click "Create bucket".

### 3. AWS LAMBDA 1 for Uploads
- Navigate to "Lambda" > "Functions"
- Create new function with params:
```html
    Option: "Author from scratch"
    Function name: "agwa-Logs-ApiToS3" 
    Runtime: Python 3.12
```
- Click "Add trigger". Select source: "API Gateway", "Use existing API" and select the api method created on previous stage.
- Paste the code in the "Code" tab:

```python
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
```
- Click "Deploy"


### 4. AWS LAMBDA 2: for Compressing
- Navigate to "Lambda" > "Functions"
- Create new function with params:
```html
    Option: "Author from scratch"
    Function name: "agwa-Logs-S3ComppressS3" 
    Runtime: Python 3.12
```
- Click "Add trigger". Fill params: 
```html
    Source: "S3"
    Bucket: "agwa-logs-original"
    Event types: "PUT"
```
- Paste the code in the "Code" tab:

```python
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
```
- Click "Deploy"




# Test

- You can test the existing system using Postman to test uploading a file.

```http
Base url: https://tckfjwcf5j.execute-api.eu-north-1.amazonaws.com/v2
Request: POST /logs
```

|   API settings   |           |
| :-------- | :------------------ |
| Header: Content-Type | text/plain |
| Header: Content-Disposition | filename="<uniq-file-name>" (example: filename="log-1.txt") |
| Header: x-api-key | F7XvZNRzgpDIXXJDsvoc9Er8XiiXMYt91musKIje |
| Body | *.txt file |




