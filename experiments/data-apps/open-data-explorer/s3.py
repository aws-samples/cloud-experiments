import streamlit as st
import boto3
import botocore
import pandas as pd
import io

s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def search_buckets():
    search = st.text_input('Search S3 bucket in your account', '')
    response = s3_client.list_buckets()
    if search:
        buckets_found = 0
        for bucket in response['Buckets']:
            if search:
                if search in bucket["Name"]:
                    buckets_found = buckets_found + 1
                    st.write(f'{bucket["Name"]}')
        if buckets_found:
            st.success(f'Listing existing **{buckets_found}** buckets containing **{search}** string')
        else:
            st.warning(f'No matching buckets found containing **{search}** string')

    else:   
        st.info('Provide string to search for listing buckets')

def list_bucket_contents():
    total_size_gb = 0
    total_files = 0
    match_size_gb = 0
    match_files = 0
    bucket = st.text_input('S3 bucket name (public bucket or private to your account)', '')
    bucket_resource = s3_resource.Bucket(bucket)
    match = st.text_input('(optional) Filter bucket contents with matching string', '')
    size_mb = st.text_input('(optional) Match files up to size in MB (0 for all sizes)', '0')
    if size_mb:
        size_mb = int(size_mb)
    else:
        size_mb = 0

    if bucket:
        for key in bucket_resource.objects.all():
            key_size_mb = key.size/1024/1024
            total_size_gb += key_size_mb
            total_files += 1
            list_check = False
            if not match:
                list_check = True
            elif match in key.key:
                list_check = True
            if list_check and not size_mb:
                match_files += 1
                match_size_gb += key_size_mb
                st.write(f'{key.key} ({key_size_mb:3.0f}MB)')
            elif list_check and key_size_mb <= size_mb:
                match_files += 1
                match_size_gb += key_size_mb
                st.write(f'{key.key} ({key_size_mb:3.0f}MB)')

        if match:
            st.info(f'Matched file size is **{match_size_gb/1024:3.1f}GB** with **{match_files}** files')            
        
        st.success(f'Bucket **{bucket}** total size is **{total_size_gb/1024:3.1f}GB** with **{total_files}** files')
    else:
        st.info('Provide bucket name to list contents')

def create_bucket():
    bucket = st.text_input('S3 bucket name to create', '')
    if bucket:
        try:
            s3_client.create_bucket(Bucket=bucket)
        except botocore.exceptions.ClientError as e:
            st.error('Bucket **' + bucket + '** could not be created. ' + e.response['Error']['Message'])
            return
        st.success('The S3 bucket **' + bucket + '** successfully created or already exists in your account')
    else:
        st.info('Provide unique bucket name to create')

def s3_select():
    bucket = st.text_input('S3 bucket name', '')
    csv = st.text_input('CSV File path and name', '')
    st.write("Example: `SELECT * FROM s3object s LIMIT 5`")
    sql = st.text_area('SQL statement', '')
    if bucket and csv and sql:
        s3_select_results = s3_client.select_object_content(
            Bucket=bucket,
            Key=csv,
            Expression=sql,
            ExpressionType='SQL',
            InputSerialization={'CSV': {"FileHeaderInfo": "Use"}},
            OutputSerialization={'JSON': {}},
        )

        for event in s3_select_results['Payload']:
            if 'Records' in event:
                df = pd.read_json(io.StringIO(event['Records']['Payload'].decode('utf-8')), lines=True)
            elif 'Stats' in event:
                st.write(f"Scanned: {int(event['Stats']['Details']['BytesScanned'])/1024/1024:5.2f}MB")            
                st.write(f"Processed: {int(event['Stats']['Details']['BytesProcessed'])/1024/1024:5.2f}MB")
                st.write(f"Returned: {int(event['Stats']['Details']['BytesReturned'])/1024/1024:5.2f}MB")
        
        st.write(df)
    else:
        st.info('Provide S3 bucket, CSV file name, and SQL statement')