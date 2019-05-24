
## Video Analytics

Analyzing video based content requires transforming from one media format (video or audio) to another format (text or numeric) while identifying relevant structure in the resulting format. This multi-media transformation requires machine learning based recognition. Analytics libraries can work on the transformed data to determine the required outcomes including visualizations and charts. The structured data in text or numeric format can also be reused as input to training new machine learning models.

In this notebook we build a simple API to display video in-place from Amazon S3 source, detect text labels based on video contents or visuals, analyze these detected labels by creating a word cloud, and search these labels matching specific text. This API can be used to build video search and analytics solutions. A potential use case is within learning management systems where the detected video labels can be used within a text based search engine to search not only among multiple videos but also within a video by matching the frame timestamp with a label. Video labels word cloud or label distribution can help analyze and visualize video content semantics in code.

Python libraries we will use include AWS SDK for Python (Boto3) to call AWS services. We will use ``pandas`` for analyzing label results as DataFrames. IPython library will provide display functionality. The ``time`` and ``io`` libraries provide utility functions used by our API. Word Cloud visualization is provided by the ``wordcloud`` library and ``matplotlib`` is the popular Python visualization library used in this notebook.


```python
import boto3
import pandas as pd
import numpy as np
from IPython.display import display, Markdown, HTML
import time
import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt
%matplotlib inline
```

Amazon Rekognition provides capabilities to recognize content within still imagery as well as motion video. To use the Rekognition API with Boto3 SDK we initialize the ``rek`` client.


```python
rek = boto3.client('rekognition')
```

### Show Video
We define our first API function for video analytics for showing video in-place within this notebook from Amazon S3 source. We can pass parameters to turn on/off autoplay and player controls. We can also specify the %size of the video to display.


```python
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
```

We are specifying the S3 bucket where stored video is present and the key representing the path to the video file. You may want to replace these values with your own stored video on S3.


```python
bucket='cloudstory'
key='notebooks-media/alexa-for-business-people.mp4'

show_video(bucket, key)
```

![Video Snapshot](https://s3.amazonaws.com/cloudstory/notebooks-media/video-analytics-snap.png)

### Video Labels Job
We can now define an API function for starting label recognition job on the S3 stored video. Label detection runs a machine learning model developed by AWS to process the video imagery detencting objects in the video and identifying these by label names coordinated with video frame timestamp. We do not need to perform any model training or deployment. The function takes S3 location as input and returns a Job ID of the label detection job in progress.


```python
def video_labels_job(bucket, key):
    video = {'S3Object': {'Bucket': bucket, 'Name': key}}
    response_detect = rek.start_label_detection(Video = video)
    return response_detect['JobId']
```


```python
jobId = video_labels_job(bucket, key)
jobId
```




    'e16110ea93a00db65a0a6a7b92e7eabcdc1d902841ee5fc77656283e457594e6'



### Video Labels Result
Depending on the length and resolution of the video the Rekognition label detection job may take several seconds to a few minutes. We will define a function to wait for this job to complete. Once the job is complete, we will publish video duration in milliseconds and framerate identified by the label detection job. We will then go on to read the response from label detection job, paginating results if these are greater than 1000 labels detected. We will then process the response and convert the resulting JSON representation into a ``pandas`` DataFrame, making the data available for analytics.


```python
def video_labels_result(jobId):
    display('In Progress...')
    response_label = rek.get_label_detection(JobId=jobId)
    while response_label['JobStatus'] == 'IN_PROGRESS':
        time.sleep(5)
        response_label = rek.get_label_detection(JobId=jobId)

    display('Getting Labels...')
    display(f"Video Duration (ms): {response_label['VideoMetadata']['DurationMillis']}")
    display(f"FrameRate: {int(response_label['VideoMetadata']['FrameRate'])}")

    labels = []
    while response_label:
        labels.extend(response_label['Labels'])
        if 'NextToken' in response_label:
            response_label = rek.get_label_detection(JobId=jobId, NextToken=response_label['NextToken']) 
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
```

The sample video we analyzed for this notebook returns 1,256 labels. Each detected label is matched with a timestamp within the video. We also get confidence score from the Rekognition model. Higher confidence generally means more accurate model results. We get insights on number of instances of a particular label or object within a frame at a particular timestamp. So if there are three people in a frame, instance count for ``Person`` label maybe three. We also get ``Parents`` or synonyms for the labels detected.


```python
df = video_labels_result(jobId)
df.head(10)
```


    'In Progress...'



    'Getting Labels...'



    'Video Duration (ms): 11345'



    'FrameRate: 23'



    'Succeeded in detecting 1256 labels.'





<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Timestamp</th>
      <th>LabelName</th>
      <th>Score</th>
      <th>Instances</th>
      <th>ParentsCount</th>
      <th>Parents</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>Apparel</td>
      <td>66.54</td>
      <td>0</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>Audience</td>
      <td>50.53</td>
      <td>0</td>
      <td>2</td>
      <td>Person, Crowd</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>Building</td>
      <td>60.53</td>
      <td>0</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>Clothing</td>
      <td>66.54</td>
      <td>0</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>4</th>
      <td>0</td>
      <td>Coat</td>
      <td>66.54</td>
      <td>0</td>
      <td>1</td>
      <td>Clothing</td>
    </tr>
    <tr>
      <th>5</th>
      <td>0</td>
      <td>Computer</td>
      <td>82.03</td>
      <td>0</td>
      <td>1</td>
      <td>Electronics</td>
    </tr>
    <tr>
      <th>6</th>
      <td>0</td>
      <td>Conference Room</td>
      <td>86.87</td>
      <td>0</td>
      <td>2</td>
      <td>Room, Indoors</td>
    </tr>
    <tr>
      <th>7</th>
      <td>0</td>
      <td>Crowd</td>
      <td>54.35</td>
      <td>0</td>
      <td>1</td>
      <td>Person</td>
    </tr>
    <tr>
      <th>8</th>
      <td>0</td>
      <td>Electronics</td>
      <td>82.03</td>
      <td>0</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>9</th>
      <td>0</td>
      <td>Furniture</td>
      <td>76.07</td>
      <td>0</td>
      <td>0</td>
      <td></td>
    </tr>
  </tbody>
</table>
</div>



### Video Labels Text
Before we run further analytics on the detected labels, we need a way to query all the labels found. The ``video_labels_text`` function returns a string of all such labels.


```python
def video_labels_text(df):
    si = io.StringIO()
    df['LabelName'].apply(lambda x: si.write(str(x + ' ')))
    s = si.getvalue()
    si.close()
    return s
```


```python
text = video_labels_text(df)
text[500:1000]
```




    'nce Room Crowd Electronics Furniture Hardware Human Indoors Interview Meeting Room Mouse Office Office Building Overcoat People Person Room Sitting Speech Suit Table Apparel Audience Building Clothing Coat Computer Conference Room Crowd Electronics Furniture Hardware Human Indoors Interview Meeting Room Mouse Office Office Building Overcoat People Person Room Sitting Speech Suit Table Apparel Audience Building Clothing Coat Computer Conference Room Crowd Electronics Furniture Hardware Human Indo'



### Video Labels Wordcloud
You will notice that many labels repeat. If we want to understand the distribution of these labels, we can simply visualize a Word Cloud based on frequency of these labels.


```python
def video_labels_wordcloud(text):
    # take relative word frequencies into account, lower max_font_size
    wordcloud = WordCloud(width = 600, height = 300, background_color = 'black', max_words = len(text),
                          max_font_size = 30, relative_scaling = .5, colormap = 'Spectral').generate(text)
    plt.figure(figsize = (20, 10))
    plt.imshow(wordcloud, interpolation = 'bilinear')
    plt.axis("off")
    plt.tight_layout(pad = 0) 
    plt.show()
```


```python
video_labels_wordcloud(text)
```

![Word Cloud](https://s3.amazonaws.com/cloudstory/notebooks-media/word-cloud-video-analytics.png)


### Video Labels Search
Now we are ready to search the labels to programmatically analyze the semantics or content of the video. The ``video_labels_search`` API matches a column within the results DataFrame with a matching string contained within the values of that column.


```python
def video_labels_search(df, column, match):
    df_result = df[df[column].str.contains(match)]
    return df_result
```

If we match ``Person`` within ``LabelName`` column we can analyze how many people feature in the video at various points in the video. You can use this API in use cases like attendance monitoring for conference rooms, training sessions, or even polling booths.


```python
video_labels_search(df, 'LabelName', 'Person')
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Timestamp</th>
      <th>LabelName</th>
      <th>Score</th>
      <th>Instances</th>
      <th>ParentsCount</th>
      <th>Parents</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>20</th>
      <td>0</td>
      <td>Person</td>
      <td>99.76</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>46</th>
      <td>166</td>
      <td>Person</td>
      <td>99.76</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>72</th>
      <td>375</td>
      <td>Person</td>
      <td>99.76</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>98</th>
      <td>583</td>
      <td>Person</td>
      <td>99.76</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>125</th>
      <td>792</td>
      <td>Person</td>
      <td>99.77</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>151</th>
      <td>959</td>
      <td>Person</td>
      <td>99.77</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>176</th>
      <td>1167</td>
      <td>Person</td>
      <td>99.77</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>198</th>
      <td>1376</td>
      <td>Person</td>
      <td>99.73</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>215</th>
      <td>1584</td>
      <td>Person</td>
      <td>99.69</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>228</th>
      <td>1793</td>
      <td>Person</td>
      <td>99.65</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>242</th>
      <td>1960</td>
      <td>Person</td>
      <td>99.63</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>259</th>
      <td>2168</td>
      <td>Person</td>
      <td>99.59</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>275</th>
      <td>2377</td>
      <td>Person</td>
      <td>99.54</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>291</th>
      <td>2585</td>
      <td>Person</td>
      <td>99.48</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>307</th>
      <td>2794</td>
      <td>Person</td>
      <td>99.40</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>326</th>
      <td>2961</td>
      <td>Person</td>
      <td>99.31</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>344</th>
      <td>3169</td>
      <td>Person</td>
      <td>99.23</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>361</th>
      <td>3378</td>
      <td>Person</td>
      <td>99.20</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>375</th>
      <td>3586</td>
      <td>Person</td>
      <td>80.42</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>385</th>
      <td>3795</td>
      <td>Person</td>
      <td>60.30</td>
      <td>2</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>409</th>
      <td>4379</td>
      <td>Person</td>
      <td>60.73</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>423</th>
      <td>4587</td>
      <td>Person</td>
      <td>80.97</td>
      <td>5</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>445</th>
      <td>4796</td>
      <td>Person</td>
      <td>99.86</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>473</th>
      <td>4963</td>
      <td>Person</td>
      <td>99.87</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>500</th>
      <td>5171</td>
      <td>Person</td>
      <td>99.87</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>523</th>
      <td>5380</td>
      <td>Person</td>
      <td>99.85</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>542</th>
      <td>5588</td>
      <td>Person</td>
      <td>99.84</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>562</th>
      <td>5797</td>
      <td>Person</td>
      <td>99.81</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>585</th>
      <td>5964</td>
      <td>Person</td>
      <td>99.79</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>610</th>
      <td>6172</td>
      <td>Person</td>
      <td>99.77</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>636</th>
      <td>6381</td>
      <td>Person</td>
      <td>99.77</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>661</th>
      <td>6589</td>
      <td>Person</td>
      <td>99.77</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>684</th>
      <td>6798</td>
      <td>Person</td>
      <td>99.76</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>703</th>
      <td>6965</td>
      <td>Person</td>
      <td>99.76</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>724</th>
      <td>7173</td>
      <td>Person</td>
      <td>99.57</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>748</th>
      <td>7382</td>
      <td>Person</td>
      <td>99.41</td>
      <td>4</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>772</th>
      <td>7590</td>
      <td>Person</td>
      <td>98.96</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>798</th>
      <td>7799</td>
      <td>Person</td>
      <td>98.73</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>824</th>
      <td>7966</td>
      <td>Person</td>
      <td>98.56</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>851</th>
      <td>8174</td>
      <td>Person</td>
      <td>98.60</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>878</th>
      <td>8383</td>
      <td>Person</td>
      <td>98.63</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>905</th>
      <td>8591</td>
      <td>Person</td>
      <td>98.92</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>932</th>
      <td>8758</td>
      <td>Person</td>
      <td>99.08</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>959</th>
      <td>8967</td>
      <td>Person</td>
      <td>99.16</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>985</th>
      <td>9175</td>
      <td>Person</td>
      <td>99.27</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1011</th>
      <td>9384</td>
      <td>Person</td>
      <td>99.35</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1037</th>
      <td>9592</td>
      <td>Person</td>
      <td>99.51</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1060</th>
      <td>9759</td>
      <td>Person</td>
      <td>99.58</td>
      <td>3</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1089</th>
      <td>9968</td>
      <td>Person</td>
      <td>99.70</td>
      <td>12</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1115</th>
      <td>10176</td>
      <td>Person</td>
      <td>99.79</td>
      <td>12</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1143</th>
      <td>10385</td>
      <td>Person</td>
      <td>99.87</td>
      <td>10</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1171</th>
      <td>10593</td>
      <td>Person</td>
      <td>99.85</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1195</th>
      <td>10760</td>
      <td>Person</td>
      <td>99.82</td>
      <td>7</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1220</th>
      <td>10969</td>
      <td>Person</td>
      <td>99.81</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>1246</th>
      <td>11177</td>
      <td>Person</td>
      <td>99.79</td>
      <td>6</td>
      <td>0</td>
      <td></td>
    </tr>
  </tbody>
</table>
</div>



We can also match ``Parents`` or synonyms of the labels detected to understand the semantics or content of the video using code. The sample video as this search suggests contains several objects under the general category of ``Computer`` which implies an office setting where the video is shot.


```python
video_labels_search(df, 'Parents', 'Computer')
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Timestamp</th>
      <th>LabelName</th>
      <th>Score</th>
      <th>Instances</th>
      <th>ParentsCount</th>
      <th>Parents</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>15</th>
      <td>0</td>
      <td>Mouse</td>
      <td>82.03</td>
      <td>1</td>
      <td>3</td>
      <td>Computer, Electronics, Hardware</td>
    </tr>
    <tr>
      <th>41</th>
      <td>166</td>
      <td>Mouse</td>
      <td>83.93</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Hardware, Computer</td>
    </tr>
    <tr>
      <th>67</th>
      <td>375</td>
      <td>Mouse</td>
      <td>85.22</td>
      <td>1</td>
      <td>3</td>
      <td>Computer, Hardware, Electronics</td>
    </tr>
    <tr>
      <th>93</th>
      <td>583</td>
      <td>Mouse</td>
      <td>87.57</td>
      <td>1</td>
      <td>3</td>
      <td>Hardware, Electronics, Computer</td>
    </tr>
    <tr>
      <th>119</th>
      <td>792</td>
      <td>Mouse</td>
      <td>89.41</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Hardware, Computer</td>
    </tr>
    <tr>
      <th>123</th>
      <td>792</td>
      <td>Pc</td>
      <td>50.10</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>146</th>
      <td>959</td>
      <td>Mouse</td>
      <td>89.70</td>
      <td>1</td>
      <td>3</td>
      <td>Computer, Hardware, Electronics</td>
    </tr>
    <tr>
      <th>172</th>
      <td>1167</td>
      <td>Mouse</td>
      <td>90.15</td>
      <td>1</td>
      <td>3</td>
      <td>Computer, Electronics, Hardware</td>
    </tr>
    <tr>
      <th>195</th>
      <td>1376</td>
      <td>Mouse</td>
      <td>73.25</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Computer, Hardware</td>
    </tr>
    <tr>
      <th>214</th>
      <td>1584</td>
      <td>Mouse</td>
      <td>55.04</td>
      <td>1</td>
      <td>3</td>
      <td>Computer, Electronics, Hardware</td>
    </tr>
    <tr>
      <th>560</th>
      <td>5797</td>
      <td>Pc</td>
      <td>50.37</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>580</th>
      <td>5964</td>
      <td>Mouse</td>
      <td>67.05</td>
      <td>1</td>
      <td>3</td>
      <td>Hardware, Computer, Electronics</td>
    </tr>
    <tr>
      <th>584</th>
      <td>5964</td>
      <td>Pc</td>
      <td>51.90</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>605</th>
      <td>6172</td>
      <td>Mouse</td>
      <td>83.16</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Hardware, Computer</td>
    </tr>
    <tr>
      <th>609</th>
      <td>6172</td>
      <td>Pc</td>
      <td>53.31</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>631</th>
      <td>6381</td>
      <td>Mouse</td>
      <td>84.25</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Hardware, Computer</td>
    </tr>
    <tr>
      <th>635</th>
      <td>6381</td>
      <td>Pc</td>
      <td>53.09</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>657</th>
      <td>6589</td>
      <td>Mouse</td>
      <td>84.47</td>
      <td>1</td>
      <td>3</td>
      <td>Computer, Electronics, Hardware</td>
    </tr>
    <tr>
      <th>660</th>
      <td>6589</td>
      <td>Pc</td>
      <td>53.37</td>
      <td>0</td>
      <td>2</td>
      <td>Computer, Electronics</td>
    </tr>
    <tr>
      <th>680</th>
      <td>6798</td>
      <td>Mouse</td>
      <td>83.63</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Hardware, Computer</td>
    </tr>
    <tr>
      <th>683</th>
      <td>6798</td>
      <td>Pc</td>
      <td>53.33</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>699</th>
      <td>6965</td>
      <td>Mouse</td>
      <td>82.93</td>
      <td>1</td>
      <td>3</td>
      <td>Hardware, Electronics, Computer</td>
    </tr>
    <tr>
      <th>702</th>
      <td>6965</td>
      <td>Pc</td>
      <td>53.48</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>720</th>
      <td>7173</td>
      <td>Mouse</td>
      <td>66.84</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Hardware, Computer</td>
    </tr>
    <tr>
      <th>723</th>
      <td>7173</td>
      <td>Pc</td>
      <td>61.54</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>744</th>
      <td>7382</td>
      <td>Laptop</td>
      <td>57.33</td>
      <td>0</td>
      <td>3</td>
      <td>Computer, Pc, Electronics</td>
    </tr>
    <tr>
      <th>747</th>
      <td>7382</td>
      <td>Pc</td>
      <td>70.09</td>
      <td>0</td>
      <td>2</td>
      <td>Computer, Electronics</td>
    </tr>
    <tr>
      <th>768</th>
      <td>7590</td>
      <td>Laptop</td>
      <td>65.76</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Computer, Electronics</td>
    </tr>
    <tr>
      <th>771</th>
      <td>7590</td>
      <td>Pc</td>
      <td>79.20</td>
      <td>0</td>
      <td>2</td>
      <td>Computer, Electronics</td>
    </tr>
    <tr>
      <th>793</th>
      <td>7799</td>
      <td>Laptop</td>
      <td>73.28</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Computer, Pc</td>
    </tr>
    <tr>
      <th>797</th>
      <td>7799</td>
      <td>Pc</td>
      <td>87.87</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>819</th>
      <td>7966</td>
      <td>Laptop</td>
      <td>81.46</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Computer, Electronics</td>
    </tr>
    <tr>
      <th>823</th>
      <td>7966</td>
      <td>Pc</td>
      <td>96.47</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>846</th>
      <td>8174</td>
      <td>Laptop</td>
      <td>81.36</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Computer, Electronics</td>
    </tr>
    <tr>
      <th>850</th>
      <td>8174</td>
      <td>Pc</td>
      <td>97.02</td>
      <td>0</td>
      <td>2</td>
      <td>Computer, Electronics</td>
    </tr>
    <tr>
      <th>873</th>
      <td>8383</td>
      <td>Laptop</td>
      <td>82.76</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Electronics, Computer</td>
    </tr>
    <tr>
      <th>877</th>
      <td>8383</td>
      <td>Pc</td>
      <td>97.62</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>900</th>
      <td>8591</td>
      <td>Laptop</td>
      <td>83.73</td>
      <td>1</td>
      <td>3</td>
      <td>Electronics, Pc, Computer</td>
    </tr>
    <tr>
      <th>904</th>
      <td>8591</td>
      <td>Pc</td>
      <td>97.65</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>927</th>
      <td>8758</td>
      <td>Laptop</td>
      <td>85.55</td>
      <td>1</td>
      <td>3</td>
      <td>Computer, Electronics, Pc</td>
    </tr>
    <tr>
      <th>931</th>
      <td>8758</td>
      <td>Pc</td>
      <td>97.95</td>
      <td>0</td>
      <td>2</td>
      <td>Computer, Electronics</td>
    </tr>
    <tr>
      <th>954</th>
      <td>8967</td>
      <td>Laptop</td>
      <td>85.10</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Computer, Electronics</td>
    </tr>
    <tr>
      <th>958</th>
      <td>8967</td>
      <td>Pc</td>
      <td>97.64</td>
      <td>0</td>
      <td>2</td>
      <td>Computer, Electronics</td>
    </tr>
    <tr>
      <th>980</th>
      <td>9175</td>
      <td>Laptop</td>
      <td>84.59</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Electronics, Computer</td>
    </tr>
    <tr>
      <th>984</th>
      <td>9175</td>
      <td>Pc</td>
      <td>97.41</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>1006</th>
      <td>9384</td>
      <td>Laptop</td>
      <td>83.80</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Computer, Electronics</td>
    </tr>
    <tr>
      <th>1010</th>
      <td>9384</td>
      <td>Pc</td>
      <td>97.35</td>
      <td>0</td>
      <td>2</td>
      <td>Computer, Electronics</td>
    </tr>
    <tr>
      <th>1032</th>
      <td>9592</td>
      <td>Laptop</td>
      <td>67.26</td>
      <td>1</td>
      <td>3</td>
      <td>Pc, Electronics, Computer</td>
    </tr>
    <tr>
      <th>1036</th>
      <td>9592</td>
      <td>Pc</td>
      <td>85.71</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>1059</th>
      <td>9759</td>
      <td>Pc</td>
      <td>72.86</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
    <tr>
      <th>1088</th>
      <td>9968</td>
      <td>Pc</td>
      <td>60.99</td>
      <td>0</td>
      <td>2</td>
      <td>Electronics, Computer</td>
    </tr>
  </tbody>
</table>
</div>



### Video Label Stats
For use cases where you want to count the number of objects in the video we can build the ``video_label_stats`` function which searches for a specific label and returns statistics for that label.


```python
def video_label_stats(df, label):
    df_stats = video_labels_search(df, column='LabelName', match=label)
    print(f'Displaying stats on number of instances for label "{label}"')
    return df_stats.describe()
```

The stats for this video and ``Person`` label suggest that at max 12 people appeared at the same time during the video, at least two people were present throughout the video, with three to four people during most of the video. If this video is monitoring utilization of an office conference room, the analytics results can help determine optimal room seating, calendar scheduling, air conditioning, and other facilities related decisions, when analyzed over a period of usage. The score stats suggest that the label was detected with 99% confidence in most cases.


```python
video_label_stats(df, 'Person')
```

    Displaying stats on number of instances for label "Person"





<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Timestamp</th>
      <th>Score</th>
      <th>Instances</th>
      <th>ParentsCount</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>count</th>
      <td>55.000000</td>
      <td>55.000000</td>
      <td>55.000000</td>
      <td>55.0</td>
    </tr>
    <tr>
      <th>mean</th>
      <td>5633.072727</td>
      <td>97.434545</td>
      <td>4.145455</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>std</th>
      <td>3366.954899</td>
      <td>8.072887</td>
      <td>2.197795</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>min</th>
      <td>0.000000</td>
      <td>60.300000</td>
      <td>2.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>25%</th>
      <td>2689.500000</td>
      <td>99.250000</td>
      <td>3.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>50%</th>
      <td>5797.000000</td>
      <td>99.690000</td>
      <td>4.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>75%</th>
      <td>8487.000000</td>
      <td>99.770000</td>
      <td>4.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>max</th>
      <td>11177.000000</td>
      <td>99.870000</td>
      <td>12.000000</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>



### Video Persons Job
We will now solve for the People Pathing problem. Amazon Rekognition can track the path people take within a video and identify the location of a person within a video frame. Use cases can include analyzing sports person performance or learning a dance step. Let's start by creating a function to submit person tracking job to Rekognition.


```python
def video_persons_job(bucket, key):
    video = {'S3Object': {'Bucket': bucket, 'Name': key}}
    response_detect = rek.start_person_tracking(Video = video)
    return response_detect['JobId']
```


```python
personsJobId = video_persons_job(bucket, key)
personsJobId
```




    'a537769e31e94d714720b956fda3a0176d6130817208134a8f2269f48ac0ba21'



### Video Persons Result
This function gets the results from person tracking job submitted earlier. It loops to check job status as it changes from ``IN_PROGRESS`` state. Then it provides some basic information about the video being analyzed like the frame rate or the duration. This is followed by creating a list of paths taken by the persons within the video. We return a DataFrame with persons identified as an index starting from zero, the timestamp of the video frame where the person is present, and the bounding box left, top, height, and width dimensions for the person identified.


```python
def video_persons_result(jobId):
    display('In Progress...')
    response_person = rek.get_person_tracking(JobId=jobId)
    while response_person['JobStatus'] == 'IN_PROGRESS':
        time.sleep(5)
        response_label = rek.get_person_tracking(JobId=jobId)

    display('Getting Person Paths...')
    display(f"Video Codec: {response_person['VideoMetadata']['Codec']}")
    display(f"Video Duration (ms): {str(response_person['VideoMetadata']['DurationMillis'])}")
    display(f"Video Format: {response_person['VideoMetadata']['Format']}")
    display(f"Video FrameRate: {int(response_person['VideoMetadata']['FrameRate'])}")

    persons = []
    while response_person:
        persons.extend(response_person['Persons'])
        if 'NextToken' in response_person:
            response_person = rek.get_person_tracking(JobId=jobId, NextToken=response_person['NextToken']) 
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
```


```python
df_persons = video_persons_result(personsJobId)
df_persons.head(10)
```


    'In Progress...'



    'Getting Person Paths...'



    'Video Codec: h264'



    'Video Duration (ms): 11345'



    'Video Format: QuickTime / MOV'



    'Video FrameRate: 23'



    'Succeeded in detecting 633 person paths.'





<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Timestamp</th>
      <th>Left</th>
      <th>Top</th>
      <th>Height</th>
      <th>Width</th>
      <th>Index</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>0.19</td>
      <td>0.33</td>
      <td>0.42</td>
      <td>0.19</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.19</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0</td>
      <td>0.42</td>
      <td>0.38</td>
      <td>0.38</td>
      <td>0.19</td>
      <td>2</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0</td>
      <td>0</td>
      <td>0.29</td>
      <td>0.69</td>
      <td>0.26</td>
      <td>3</td>
    </tr>
    <tr>
      <th>4</th>
      <td>41</td>
      <td>0.19</td>
      <td>0.33</td>
      <td>0.42</td>
      <td>0.19</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <td>41</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.19</td>
      <td>1</td>
    </tr>
    <tr>
      <th>6</th>
      <td>41</td>
      <td>0.42</td>
      <td>0.38</td>
      <td>0.38</td>
      <td>0.19</td>
      <td>2</td>
    </tr>
    <tr>
      <th>7</th>
      <td>41</td>
      <td>0</td>
      <td>0.28</td>
      <td>0.69</td>
      <td>0.26</td>
      <td>3</td>
    </tr>
    <tr>
      <th>8</th>
      <td>125</td>
      <td>0.19</td>
      <td>0.33</td>
      <td>0.42</td>
      <td>0.19</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <td>125</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
  </tbody>
</table>
</div>



### Video Person Path
This function returns the paths matching a person identified by an index. In this specific example we are searching for the lady sitting in the center of the table as the video begins. Note how the timestamp shows her presence in the video during first 2 seconds of the video, then reappearance around between the 6 and 8 seconds timeframe. Also note how the top and left attributes do not change for the bounding box indicating the lady does not appear to move within the video.


```python
def video_person_path(df, person):
    df_result = df[df['Index'] == person]
    return df_result
```


```python
video_person_path(df_persons, 1)
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Timestamp</th>
      <th>Left</th>
      <th>Top</th>
      <th>Height</th>
      <th>Width</th>
      <th>Index</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.19</td>
      <td>1</td>
    </tr>
    <tr>
      <th>5</th>
      <td>41</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.19</td>
      <td>1</td>
    </tr>
    <tr>
      <th>9</th>
      <td>125</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>13</th>
      <td>166</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>17</th>
      <td>250</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>21</th>
      <td>291</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>25</th>
      <td>375</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>29</th>
      <td>458</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>33</th>
      <td>500</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>37</th>
      <td>583</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>41</th>
      <td>625</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>45</th>
      <td>709</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>49</th>
      <td>792</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>53</th>
      <td>834</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>57</th>
      <td>917</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>61</th>
      <td>959</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>65</th>
      <td>1042</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>69</th>
      <td>1126</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>73</th>
      <td>1167</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>77</th>
      <td>1251</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>81</th>
      <td>1292</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>85</th>
      <td>1376</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>89</th>
      <td>1459</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>93</th>
      <td>1501</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>97</th>
      <td>1584</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>296</th>
      <td>5797</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>300</th>
      <td>5839</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>304</th>
      <td>5922</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>308</th>
      <td>5964</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>312</th>
      <td>6047</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>316</th>
      <td>6131</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>320</th>
      <td>6172</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>324</th>
      <td>6256</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>328</th>
      <td>6297</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>332</th>
      <td>6381</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>336</th>
      <td>6464</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>340</th>
      <td>6506</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>344</th>
      <td>6589</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>348</th>
      <td>6631</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.36</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>352</th>
      <td>6715</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>356</th>
      <td>6798</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>360</th>
      <td>6840</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>364</th>
      <td>6923</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>368</th>
      <td>6965</td>
      <td>0.67</td>
      <td>0.37</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>372</th>
      <td>7048</td>
      <td>0.67</td>
      <td>0.38</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>376</th>
      <td>7132</td>
      <td>0.67</td>
      <td>0.38</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>380</th>
      <td>7173</td>
      <td>0.67</td>
      <td>0.38</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>384</th>
      <td>7257</td>
      <td>0.67</td>
      <td>0.38</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>388</th>
      <td>7298</td>
      <td>0.67</td>
      <td>0.38</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
    <tr>
      <th>392</th>
      <td>7382</td>
      <td>0.67</td>
      <td>0.38</td>
      <td>0.35</td>
      <td>0.2</td>
      <td>1</td>
    </tr>
  </tbody>
</table>
</div>



### Video Person Timeframe
We now write a function to return persons found within a given timeframe of the video. In this example, notice how the person identified by the index 16 is "taller" than the other to persons within the frame. Around the 7 seconds timestamp, the lady in purple dress is standing while the other two persons in the room are seated at the table. The top and left values also change slightly between the two appearances of the lady within the video indicating slight movement.


```python
def video_person_timeframe(df, start, end):
    df_result = df[(df['Timestamp'] >= start) & (df['Timestamp'] <= end)]
    return df_result
```


```python
video_person_timeframe(df_persons, 7900, 9000)
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Timestamp</th>
      <th>Left</th>
      <th>Top</th>
      <th>Height</th>
      <th>Width</th>
      <th>Index</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>409</th>
      <td>7924</td>
      <td>0.46</td>
      <td>0.17</td>
      <td>0.76</td>
      <td>0.22</td>
      <td>14</td>
    </tr>
    <tr>
      <th>410</th>
      <td>7924</td>
      <td>0</td>
      <td>0.24</td>
      <td>0.71</td>
      <td>0.26</td>
      <td>15</td>
    </tr>
    <tr>
      <th>411</th>
      <td>7924</td>
      <td>0.68</td>
      <td>0.06</td>
      <td>0.94</td>
      <td>0.32</td>
      <td>16</td>
    </tr>
    <tr>
      <th>412</th>
      <td>7966</td>
      <td>0.45</td>
      <td>0.16</td>
      <td>0.77</td>
      <td>0.22</td>
      <td>14</td>
    </tr>
    <tr>
      <th>413</th>
      <td>7966</td>
      <td>0</td>
      <td>0.24</td>
      <td>0.71</td>
      <td>0.26</td>
      <td>15</td>
    </tr>
    <tr>
      <th>414</th>
      <td>7966</td>
      <td>0.68</td>
      <td>0.06</td>
      <td>0.94</td>
      <td>0.31</td>
      <td>16</td>
    </tr>
    <tr>
      <th>415</th>
      <td>8049</td>
      <td>0.44</td>
      <td>0.17</td>
      <td>0.76</td>
      <td>0.2</td>
      <td>14</td>
    </tr>
    <tr>
      <th>416</th>
      <td>8049</td>
      <td>0</td>
      <td>0.25</td>
      <td>0.71</td>
      <td>0.26</td>
      <td>15</td>
    </tr>
    <tr>
      <th>417</th>
      <td>8049</td>
      <td>0.68</td>
      <td>0.06</td>
      <td>0.94</td>
      <td>0.32</td>
      <td>16</td>
    </tr>
    <tr>
      <th>418</th>
      <td>8133</td>
      <td>0.43</td>
      <td>0.17</td>
      <td>0.76</td>
      <td>0.19</td>
      <td>14</td>
    </tr>
    <tr>
      <th>419</th>
      <td>8133</td>
      <td>0</td>
      <td>0.25</td>
      <td>0.71</td>
      <td>0.26</td>
      <td>15</td>
    </tr>
    <tr>
      <th>420</th>
      <td>8174</td>
      <td>0.43</td>
      <td>0.17</td>
      <td>0.76</td>
      <td>0.19</td>
      <td>14</td>
    </tr>
    <tr>
      <th>421</th>
      <td>8174</td>
      <td>0</td>
      <td>0.25</td>
      <td>0.71</td>
      <td>0.26</td>
      <td>15</td>
    </tr>
    <tr>
      <th>422</th>
      <td>8258</td>
      <td>0.41</td>
      <td>0.16</td>
      <td>0.77</td>
      <td>0.2</td>
      <td>14</td>
    </tr>
    <tr>
      <th>423</th>
      <td>8258</td>
      <td>0</td>
      <td>0.25</td>
      <td>0.71</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>424</th>
      <td>8299</td>
      <td>0.4</td>
      <td>0.16</td>
      <td>0.77</td>
      <td>0.2</td>
      <td>14</td>
    </tr>
    <tr>
      <th>425</th>
      <td>8299</td>
      <td>0</td>
      <td>0.25</td>
      <td>0.71</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>426</th>
      <td>8383</td>
      <td>0.39</td>
      <td>0.17</td>
      <td>0.75</td>
      <td>0.23</td>
      <td>14</td>
    </tr>
    <tr>
      <th>427</th>
      <td>8383</td>
      <td>0</td>
      <td>0.25</td>
      <td>0.71</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>428</th>
      <td>8425</td>
      <td>0.38</td>
      <td>0.17</td>
      <td>0.75</td>
      <td>0.23</td>
      <td>14</td>
    </tr>
    <tr>
      <th>429</th>
      <td>8425</td>
      <td>0</td>
      <td>0.25</td>
      <td>0.71</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>430</th>
      <td>8508</td>
      <td>0.38</td>
      <td>0.18</td>
      <td>0.75</td>
      <td>0.23</td>
      <td>14</td>
    </tr>
    <tr>
      <th>431</th>
      <td>8508</td>
      <td>0</td>
      <td>0.24</td>
      <td>0.72</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>432</th>
      <td>8591</td>
      <td>0.38</td>
      <td>0.16</td>
      <td>0.76</td>
      <td>0.23</td>
      <td>14</td>
    </tr>
    <tr>
      <th>433</th>
      <td>8591</td>
      <td>0.01</td>
      <td>0.25</td>
      <td>0.68</td>
      <td>0.28</td>
      <td>15</td>
    </tr>
    <tr>
      <th>434</th>
      <td>8591</td>
      <td>0.66</td>
      <td>0.05</td>
      <td>0.94</td>
      <td>0.34</td>
      <td>16</td>
    </tr>
    <tr>
      <th>435</th>
      <td>8633</td>
      <td>0.39</td>
      <td>0.16</td>
      <td>0.76</td>
      <td>0.22</td>
      <td>14</td>
    </tr>
    <tr>
      <th>436</th>
      <td>8633</td>
      <td>0.01</td>
      <td>0.25</td>
      <td>0.68</td>
      <td>0.28</td>
      <td>15</td>
    </tr>
    <tr>
      <th>437</th>
      <td>8633</td>
      <td>0.67</td>
      <td>0.05</td>
      <td>0.94</td>
      <td>0.33</td>
      <td>16</td>
    </tr>
    <tr>
      <th>438</th>
      <td>8717</td>
      <td>0.38</td>
      <td>0.16</td>
      <td>0.77</td>
      <td>0.23</td>
      <td>14</td>
    </tr>
    <tr>
      <th>439</th>
      <td>8717</td>
      <td>0.01</td>
      <td>0.25</td>
      <td>0.68</td>
      <td>0.28</td>
      <td>15</td>
    </tr>
    <tr>
      <th>440</th>
      <td>8758</td>
      <td>0.39</td>
      <td>0.16</td>
      <td>0.77</td>
      <td>0.22</td>
      <td>14</td>
    </tr>
    <tr>
      <th>441</th>
      <td>8758</td>
      <td>0.01</td>
      <td>0.25</td>
      <td>0.68</td>
      <td>0.28</td>
      <td>15</td>
    </tr>
    <tr>
      <th>442</th>
      <td>8842</td>
      <td>0.39</td>
      <td>0.15</td>
      <td>0.77</td>
      <td>0.22</td>
      <td>14</td>
    </tr>
    <tr>
      <th>443</th>
      <td>8842</td>
      <td>0.01</td>
      <td>0.25</td>
      <td>0.69</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>444</th>
      <td>8842</td>
      <td>0.67</td>
      <td>0.05</td>
      <td>0.94</td>
      <td>0.33</td>
      <td>16</td>
    </tr>
    <tr>
      <th>445</th>
      <td>8925</td>
      <td>0.39</td>
      <td>0.15</td>
      <td>0.77</td>
      <td>0.22</td>
      <td>14</td>
    </tr>
    <tr>
      <th>446</th>
      <td>8925</td>
      <td>0.01</td>
      <td>0.24</td>
      <td>0.7</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>447</th>
      <td>8925</td>
      <td>0.67</td>
      <td>0.05</td>
      <td>0.95</td>
      <td>0.33</td>
      <td>16</td>
    </tr>
    <tr>
      <th>448</th>
      <td>8967</td>
      <td>0.39</td>
      <td>0.15</td>
      <td>0.77</td>
      <td>0.22</td>
      <td>14</td>
    </tr>
    <tr>
      <th>449</th>
      <td>8967</td>
      <td>0.01</td>
      <td>0.23</td>
      <td>0.7</td>
      <td>0.27</td>
      <td>15</td>
    </tr>
    <tr>
      <th>450</th>
      <td>8967</td>
      <td>0.67</td>
      <td>0.05</td>
      <td>0.95</td>
      <td>0.33</td>
      <td>16</td>
    </tr>
  </tbody>
</table>
</div>



### Video Persons Frequency
Now we are writing a simple function to indicate how frequently a person identified by an index appears during the entire video. In this example, the three persons sitting on the table facing the camera appear for during most of the video. One also notes that the API recognizes 22 persons during the course of the video. One may want to cross verify this result with the video and the label detection output which identifies 12 persons at max within a frame.


```python
def video_persons_frequency(df):
    return df.groupby('Index')['Timestamp'].nunique()
```


```python
video_persons_frequency(df_persons)
```




    Index
    0     50
    1     50
    2     50
    3     25
    4     34
    5     34
    6     29
    7     25
    8     23
    9     28
    10    20
    11    23
    12     6
    13    25
    14    36
    15    33
    16    16
    17    23
    18    18
    19    23
    20    23
    21    23
    22    16
    Name: Timestamp, dtype: int64


