import boto3
import botocore
import pandas as pd
import numpy as np
import io
import json
import time
import logging
import seaborn as sns
import matplotlib.pyplot as plt
from IPython.display import display, Markdown, Image, HTML
from wordcloud import WordCloud

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
glue = boto3.client('glue')
athena = boto3.client('athena')
rekognition = boto3.client('rekognition','us-east-1')
comprehend = boto3.client('comprehend', 'us-east-1')

# Function library from https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/exploring-data

def create_bucket(bucket):
    try:
        s3.create_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        logging.error(e)
        return 'Bucket ' + bucket + ' could not be created.'
    return 'Created or already exists ' + bucket + ' bucket.'

def list_buckets(match=''):
    response = s3.list_buckets()
    if match:
        print(f'Existing buckets containing "{match}" string:')
    else:
        print('All existing buckets:')
    for bucket in response['Buckets']:
        if match:
            if match in bucket["Name"]:
                print(f'  {bucket["Name"]}')

def list_bucket_contents(bucket, match='', size_mb=0):
    bucket_resource = s3_resource.Bucket(bucket)
    total_size_gb = 0
    total_files = 0
    match_size_gb = 0
    match_files = 0
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
            print(f'{key.key} ({key_size_mb:3.0f}MB)')
        elif list_check and key_size_mb <= size_mb:
            match_files += 1
            match_size_gb += key_size_mb
            print(f'{key.key} ({key_size_mb:3.0f}MB)')

    if match:
        print(f'Matched file size is {match_size_gb/1024:3.1f}GB with {match_files} files')            
    
    print(f'Bucket {bucket} total size is {total_size_gb/1024:3.1f}GB with {total_files} files')

def preview_csv_dataset(bucket, key, rows=10):
    data_source = {
            'Bucket': bucket,
            'Key': key
        }
    # Generate the URL to get Key from Bucket
    url = s3.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = data_source
    )

    data = pd.read_csv(url, nrows=rows)
    return data

def key_exists(bucket, key):
    try:
        s3_resource.Object(bucket, key).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The key does not exist.
            return(False)
        else:
            # Something else has gone wrong.
            raise
    else:
        # The key does exist.
        return(True)

def copy_among_buckets(from_bucket, from_key, to_bucket, to_key):
    if not key_exists(to_bucket, to_key):
        s3_resource.meta.client.copy({'Bucket': from_bucket, 'Key': from_key}, 
                                        to_bucket, to_key)        
        print(f'File {to_key} saved to S3 bucket {to_bucket}')
    else:
        print(f'File {to_key} already exists in S3 bucket {to_bucket}') 

def s3_select(bucket, key, statement):
    import io

    s3_select_results = s3.select_object_content(
        Bucket=bucket,
        Key=key,
        Expression=statement,
        ExpressionType='SQL',
        InputSerialization={'CSV': {"FileHeaderInfo": "Use"}},
        OutputSerialization={'JSON': {}},
    )

    for event in s3_select_results['Payload']:
        if 'Records' in event:
            df = pd.read_json(io.StringIO(event['Records']['Payload'].decode('utf-8')), lines=True)
        elif 'Stats' in event:
            print(f"Scanned: {int(event['Stats']['Details']['BytesScanned'])/1024/1024:5.2f}MB")            
            print(f"Processed: {int(event['Stats']['Details']['BytesProcessed'])/1024/1024:5.2f}MB")
            print(f"Returned: {int(event['Stats']['Details']['BytesReturned'])/1024/1024:5.2f}MB")
    return (df)


# Function library from https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/optimizing-data

def list_glue_databases():
    glue_database = glue.get_databases()

    for db in glue_database['DatabaseList']:
        print(db['Name'])

def list_glue_tables(database, verbose=True):
    glue_tables = glue.get_tables(DatabaseName=database)
    
    for table in glue_tables['TableList']:
        display(Markdown('**Table: ' + table['Name'] + '**'))
        display(Markdown('Location: ' + table['StorageDescriptor']['Location']))
        created = table['CreatedBy'].split('/')
        display(Markdown('Created by: ' + created[-1]))
        if verbose and created[-1] == 'AWS Crawler':
            display(Markdown(f'Records: {int(table["Parameters"]["recordCount"]):,}'))
            display(Markdown(f'Average Record Size: {table["Parameters"]["averageRecordSize"]} Bytes'))
            display(Markdown(f'Dataset Size: {float(table["Parameters"]["sizeKey"])/1024/1024:3.0f} MB'))
            display(Markdown(f'Crawler: {table["Parameters"]["UPDATED_BY_CRAWLER"]}'))
        if verbose:
            df_columns = pd.DataFrame.from_dict(table["StorageDescriptor"]["Columns"])
            display(df_columns[['Name', 'Type']])
            display(Markdown('---'))

def athena_query(query, bucket, folder):
    output = 's3://' + bucket + '/' + folder + '/'
    response = athena.start_query_execution(QueryString=query, 
                                        ResultConfiguration={'OutputLocation': output})
    qid = response['QueryExecutionId']
    response = athena.get_query_execution(QueryExecutionId=qid)
    state = response['QueryExecution']['Status']['State']
    while state == 'RUNNING':
        response = athena.get_query_execution(QueryExecutionId=qid)
        state = response['QueryExecution']['Status']['State']
    key = folder + '/' + qid + '.csv'
    data_source = {'Bucket': bucket, 'Key': key}
    url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = data_source)
    data = pd.read_csv(url)
    return data

def heatmap(corr):
    sns.set(style="white")

    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(11, 9))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, center=0, annot=True, fmt="3.2f",
                square=True, linewidths=.5, cbar_kws={"shrink": .5})

# Function library from https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/ai-services

def show_image(bucket, key, img_width = 500):
    # [TODO] Load non-public images
    return Image(url='https://s3.amazonaws.com/' + bucket + '/' + key, width=img_width)

def image_labels(bucket, key):
    image_object = {'S3Object':{'Bucket': bucket,'Name': key}}

    response = rekognition.detect_labels(Image=image_object)
    for label in response['Labels']:
        print('{} ({:.0f}%)'.format(label['Name'], label['Confidence']))

def image_label_count(bucket, key, match):    
    image_object = {'S3Object':{'Bucket': bucket,'Name': key}}

    response = rekognition.detect_labels(Image=image_object)
    count = 0
    for label in response['Labels']:
        if match in label['Name']:
            for instance in label['Instances']:
                count += 1
    print(f'Found {match} {count} times.')

def image_text(bucket, key, sort_column='', parents=True):
    response = rekognition.detect_text(Image={'S3Object':{'Bucket':bucket,'Name': key}})
    df = pd.read_json(io.StringIO(json.dumps(response['TextDetections'])))
    df['Width'] = df['Geometry'].apply(lambda x: x['BoundingBox']['Width'])
    df['Height'] = df['Geometry'].apply(lambda x: x['BoundingBox']['Height'])
    df['Left'] = df['Geometry'].apply(lambda x: x['BoundingBox']['Left'])
    df['Top'] = df['Geometry'].apply(lambda x: x['BoundingBox']['Top'])
    df = df.drop(columns=['Geometry'])
    if sort_column:
        df = df.sort_values([sort_column])
    if not parents:
        df = df[df['ParentId'] > 0]
    return df

def detect_celebs(bucket, key, sort_column=''):
    image_object = {'S3Object':{'Bucket': bucket,'Name': key}}

    response = rekognition.recognize_celebrities(Image=image_object)
    df = pd.DataFrame(response['CelebrityFaces'])
    df['Width'] = df['Face'].apply(lambda x: x['BoundingBox']['Width'])
    df['Height'] = df['Face'].apply(lambda x: x['BoundingBox']['Height'])
    df['Left'] = df['Face'].apply(lambda x: x['BoundingBox']['Left'])
    df['Top'] = df['Face'].apply(lambda x: x['BoundingBox']['Top'])
    df = df.drop(columns=['Face'])
    if sort_column:
        df = df.sort_values([sort_column])
    return(df)

def comprehend_syntax(text): 
    response = comprehend.detect_syntax(Text=text, LanguageCode='en')
    df = pd.read_json(io.StringIO(json.dumps(response['SyntaxTokens'])))
    df['Tag'] = df['PartOfSpeech'].apply(lambda x: x['Tag'])
    df['Score'] = df['PartOfSpeech'].apply(lambda x: x['Score'])
    df = df.drop(columns=['PartOfSpeech'])
    return df

def comprehend_entities(text):
    response = comprehend.detect_entities(Text=text, LanguageCode='en')
    df = pd.read_json(io.StringIO(json.dumps(response['Entities'])))
    return df

def comprehend_phrases(text):
    response = comprehend.detect_key_phrases(Text=text, LanguageCode='en')
    df = pd.read_json(io.StringIO(json.dumps(response['KeyPhrases'])))
    return df

def comprehend_sentiment(text):
    response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
    return response['SentimentScore']
    
def show_video(bucket, key, size=100, autoplay=False, controls=True):
    source = f'https://s3.amazonaws.com/{bucket}/{key}'
    html = '''
    <div align="middle">
        <video width="{}%"{}{}>
        <source src="{}" type="video/mp4">
        </video>
    </div>
    '''
    html = html.format(size, 
                    ' controls' if controls else '', 
                    ' autoplay' if autoplay else '', 
                    source)
    return HTML(html)

def video_labels_job(bucket, key):
    video = {'S3Object': {'Bucket': bucket, 'Name': key}}
    response_detect = rekognition.start_label_detection(Video = video)
    return response_detect['JobId']


def video_labels_result(jobId):
    display('In Progress...')
    response_label = rekognition.get_label_detection(JobId=jobId)
    while response_label['JobStatus'] == 'IN_PROGRESS':
        time.sleep(5)
        response_label = rekognition.get_label_detection(JobId=jobId)

    display('Getting Labels...')
    display(f"Video Duration (ms): {response_label['VideoMetadata']['DurationMillis']}")
    display(f"FrameRate: {int(response_label['VideoMetadata']['FrameRate'])}")

    labels = []
    while response_label:
        labels.extend(response_label['Labels'])
        if 'NextToken' in response_label:
            response_label = rekognition.get_label_detection(JobId=jobId, NextToken=response_label['NextToken']) 
        else:
            response_label = None
    
    display(f'Succeeded in detecting {len(labels)} labels.')
    
    df = pd.DataFrame(labels)
    df['LabelName'] = df['Label'].apply(lambda x: x['Name'])
    df['Score'] = df['Label'].apply(lambda x: round(float(x['Confidence']), 2))
    df['Instances'] = df['Label'].apply(lambda x: len(x['Instances']) if x['Instances'] else 0)
    df['ParentsCount'] = df['Label'].apply(lambda x: len(x['Parents']))
    df['Parents'] = df['Label'].apply(lambda x: ', '.join(map(lambda x : x['Name'], x['Parents'])))
    df = df.drop(columns=['Label'])
    return df    

def video_labels_text(df):
    si = io.StringIO()
    df['LabelName'].apply(lambda x: si.write(str(x + ' ')))
    s = si.getvalue()
    si.close()
    return s

def video_labels_wordcloud(text):
    # take relative word frequencies into account, lower max_font_size
    wordcloud = WordCloud(width = 600, height = 300, background_color = 'black', max_words = len(text),
                        max_font_size = 30, relative_scaling = .5, colormap = 'Spectral').generate(text)
    plt.figure(figsize = (20, 10))
    plt.imshow(wordcloud, interpolation = 'bilinear')
    plt.axis("off")
    plt.tight_layout(pad = 0) 
    plt.show()

def video_labels_search(df, column, match):
    df_result = df[df[column].str.contains(match)]
    return df_result

def video_label_stats(df, label):
    df_stats = video_labels_search(df, column='LabelName', match=label)
    print(f'Displaying stats on number of instances for label "{label}"')
    return df_stats.describe()

def video_persons_job(bucket, key):
    video = {'S3Object': {'Bucket': bucket, 'Name': key}}
    response_detect = rekognition.start_person_tracking(Video = video)
    return response_detect['JobId']    

def video_persons_result(jobId):
    display('In Progress...')
    response_person = rekognition.get_person_tracking(JobId=jobId)
    while response_person['JobStatus'] == 'IN_PROGRESS':
        time.sleep(5)
        response_label = rekognition.get_person_tracking(JobId=jobId)

    display('Getting Person Paths...')
    display(f"Video Codec: {response_person['VideoMetadata']['Codec']}")
    display(f"Video Duration (ms): {str(response_person['VideoMetadata']['DurationMillis'])}")
    display(f"Video Format: {response_person['VideoMetadata']['Format']}")
    display(f"Video FrameRate: {int(response_person['VideoMetadata']['FrameRate'])}")

    persons = []
    while response_person:
        persons.extend(response_person['Persons'])
        if 'NextToken' in response_person:
            response_person = rekognition.get_person_tracking(JobId=jobId, NextToken=response_person['NextToken']) 
        else:
            response_person = None
    
    display(f'Succeeded in detecting {len(persons)} person paths.')
    
    df = pd.DataFrame(persons)
    df['Left'] = df['Person'].apply(lambda x: round(x['BoundingBox']['Left'], 2) if 'BoundingBox' in x else '')
    df['Top'] = df['Person'].apply(lambda x: round(x['BoundingBox']['Top'], 2) if 'BoundingBox' in x else '')
    df['Height'] = df['Person'].apply(lambda x: round(x['BoundingBox']['Height'], 2) if 'BoundingBox' in x else '')
    df['Width'] = df['Person'].apply(lambda x: round(x['BoundingBox']['Width'], 2) if 'BoundingBox' in x else '')
    df['Index'] = df['Person'].apply(lambda x: x['Index'])
    df = df.drop(columns=['Person'])

    return df

def video_person_path(df, person):
    df_result = df[df['Index'] == person]
    return df_result

def video_person_timeframe(df, start, end):
    df_result = df[(df['Timestamp'] >= start) & (df['Timestamp'] <= end)]
    return df_result

def video_persons_frequency(df):
    return df.groupby('Index')['Timestamp'].nunique()