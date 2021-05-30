
## Using AI Services for Analyzing Public Data
by Manav Sehgal | on APR 30 2019

So far we have been working with structured data in flat files as our data source. What if the source is images and unstructured text. AWS AI services provide vision, transcription, translation, personalization, and forecasting capabilities without the need for training and deploying machine learning models. AWS manages the machine learning complexity, you just focus on the problem at hand and send required inputs for analysis and receive output from these services within your applications.

Extending our open data analytics use case to New York Traffic let us use the AWS AI services to turn open data available in social media, Wikipedia, and other sources into structured datasets and insights.

We will start by importing dependencies for AWS SDK, Python Data Frames, file operations, handeling JSON data, and display formatting. We will initialize the Rekognition client for use in the rest of this notebook.


```python
import boto3
import pandas as pd
import io
import json
from IPython.display import display, Markdown, Image

rekognition = boto3.client('rekognition','us-east-1')
image_bucket = 'open-data-analytics-taxi-trips'
```

### Show Image
We will work with a number of images so we need a way to show these images within this notebook. Our function creates a public image URL based on S3 bucket and key as input.


```python
def show_image(bucket, key, img_width = 500):
    # [TODO] Load non-public images
    return Image(url='https://s3.amazonaws.com/' + bucket + '/' + key, width=img_width)
```


```python
show_image(image_bucket, 'images/traffic-in-manhattan.jpg', 1024)
```




<img src="https://s3.amazonaws.com/open-data-analytics-taxi-trips/images/traffic-in-manhattan.jpg" width="1024"/>



### Image Labels
One of use cases for traffic analytics is processing traffic CCTV imagery or social media uploads. Let's consider a traffic location where depending on number of cars, trucks, and pedestrians we can identify if there is a traffic jam. This insight can be used to better manage flow of traffic around the location and plan ahead for future use of this route.

First step in this kind of analytics is to recognize that we are actually looking at an image which may represent a traffic jam. We create ``image_labels`` function which uses ``detect_lables`` Rekognition API to detect objects within an image. The function prints labels detected with confidence score.

In the given example notice somewhere in the middle of the labels listing at 73% confidence the Rekognition computer vision model has actually determined a traffic jam.


```python
def image_labels(bucket, key):
    image_object = {'S3Object':{'Bucket': bucket,'Name': key}}

    response = rekognition.detect_labels(Image=image_object)
    for label in response['Labels']:
        print('{} ({:.0f}%)'.format(label['Name'], label['Confidence']))
```


```python
image_labels(image_bucket, 'images/traffic-in-manhattan.jpg')
```

    Vehicle (100%)
    Automobile (100%)
    Transportation (100%)
    Car (100%)
    Human (99%)
    Person (99%)
    Truck (98%)
    Machine (96%)
    Wheel (96%)
    Clothing (87%)
    Apparel (87%)
    Footwear (87%)
    Shoe (87%)
    Road (75%)
    Traffic Jam (73%)
    City (73%)
    Urban (73%)
    Metropolis (73%)
    Building (73%)
    Town (73%)
    Cab (71%)
    Taxi (71%)
    Traffic Light (68%)
    Light (68%)
    Neighborhood (62%)
    People (62%)
    Pedestrian (59%)


### Image Label Count
Now that we have a label detecting a traffic jam and some of the ingredients of a busy traffic location like pedestrians, trucks, cars, let us determine quantitative data for benchmarking different traffic locations. If we can count the number of cars, trucks, and persons in the image we can compare these numbers with other images. Our function does just that, it counts the number of instances of a matching label.


```python
def image_label_count(bucket, key, match):    
    image_object = {'S3Object':{'Bucket': bucket,'Name': key}}

    response = rekognition.detect_labels(Image=image_object)
    count = 0
    for label in response['Labels']:
        if match in label['Name']:
            for instance in label['Instances']:
                count += 1
    print(f'Found {match} {count} times.')
```


```python
image_label_count(image_bucket, 'images/traffic-in-manhattan.jpg', 'Car')
```

    Found Car 9 times.



```python
image_label_count(image_bucket, 'images/traffic-in-manhattan.jpg', 'Truck')
```

    Found Truck 4 times.



```python
image_label_count(image_bucket, 'images/traffic-in-manhattan.jpg', 'Person')
```

    Found Person 8 times.


### Image Text
Another use case of traffic location analytics using social media content is to understand more about a traffic location and instance if there is an incident reported, like an accident, jam, or VIP movement. For a computer program to understand a random traffic location, it may help to capture any text within the image. The ``image_text`` function uses Amazon Rekognition service to detect text in an image.

You will notice that the text recognition is capable to read blurry text like "The Lion King", text which is at a perspective like the bus route, text which may be ignored by the human eye like the address below the shoes banner, and even the text representing the taxi number. Suddenly the image starts telling a story programmatically, about what time it may represent, what are the landmarks, which bus route, which taxi number was on streets, and so on.


```python
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
```


```python
show_image(image_bucket, 'images/nyc-taxi-signs.jpeg', 1024)
```




<img src="https://s3.amazonaws.com/open-data-analytics-taxi-trips/images/nyc-taxi-signs.jpeg" width="1024"/>



Sorting on ``Top`` column will keep the horizontal text together.


```python
image_text(image_bucket, 'images/nyc-taxi-signs.jpeg', sort_column='Top', parents=False)
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Confidence</th>
      <th>DetectedText</th>
      <th>Id</th>
      <th>ParentId</th>
      <th>Type</th>
      <th>Width</th>
      <th>Height</th>
      <th>Left</th>
      <th>Top</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>14</th>
      <td>91.874588</td>
      <td>WAY</td>
      <td>15</td>
      <td>1.0</td>
      <td>WORD</td>
      <td>0.028470</td>
      <td>0.019385</td>
      <td>0.599400</td>
      <td>0.109109</td>
    </tr>
    <tr>
      <th>15</th>
      <td>83.133957</td>
      <td>6ASW</td>
      <td>14</td>
      <td>1.0</td>
      <td>WORD</td>
      <td>0.034089</td>
      <td>0.018404</td>
      <td>0.570143</td>
      <td>0.126126</td>
    </tr>
    <tr>
      <th>17</th>
      <td>94.518997</td>
      <td>HAN'S</td>
      <td>17</td>
      <td>2.0</td>
      <td>WORD</td>
      <td>0.070971</td>
      <td>0.032111</td>
      <td>0.388597</td>
      <td>0.187187</td>
    </tr>
    <tr>
      <th>16</th>
      <td>99.643578</td>
      <td>DELI</td>
      <td>16</td>
      <td>2.0</td>
      <td>WORD</td>
      <td>0.080892</td>
      <td>0.041151</td>
      <td>0.281320</td>
      <td>0.201201</td>
    </tr>
    <tr>
      <th>18</th>
      <td>90.439888</td>
      <td>&amp;</td>
      <td>18</td>
      <td>3.0</td>
      <td>WORD</td>
      <td>0.027007</td>
      <td>0.044044</td>
      <td>0.364591</td>
      <td>0.212212</td>
    </tr>
    <tr>
      <th>19</th>
      <td>99.936119</td>
      <td>GROCERY</td>
      <td>19</td>
      <td>3.0</td>
      <td>WORD</td>
      <td>0.150999</td>
      <td>0.042149</td>
      <td>0.399850</td>
      <td>0.217217</td>
    </tr>
    <tr>
      <th>20</th>
      <td>81.925537</td>
      <td>ZiGi</td>
      <td>20</td>
      <td>4.0</td>
      <td>WORD</td>
      <td>0.027007</td>
      <td>0.023035</td>
      <td>0.595649</td>
      <td>0.265265</td>
    </tr>
    <tr>
      <th>21</th>
      <td>95.180290</td>
      <td>SHOES</td>
      <td>21</td>
      <td>5.0</td>
      <td>WORD</td>
      <td>0.041695</td>
      <td>0.019078</td>
      <td>0.621906</td>
      <td>0.269269</td>
    </tr>
    <tr>
      <th>22</th>
      <td>91.584435</td>
      <td>X29CONEYSL</td>
      <td>23</td>
      <td>5.0</td>
      <td>WORD</td>
      <td>0.108448</td>
      <td>0.038509</td>
      <td>0.887472</td>
      <td>0.279279</td>
    </tr>
    <tr>
      <th>23</th>
      <td>90.353638</td>
      <td>x29</td>
      <td>24</td>
      <td>5.0</td>
      <td>WORD</td>
      <td>0.038896</td>
      <td>0.033245</td>
      <td>0.888972</td>
      <td>0.282282</td>
    </tr>
    <tr>
      <th>24</th>
      <td>96.308746</td>
      <td>647</td>
      <td>22</td>
      <td>5.0</td>
      <td>WORD</td>
      <td>0.018755</td>
      <td>0.016016</td>
      <td>0.747937</td>
      <td>0.293293</td>
    </tr>
    <tr>
      <th>25</th>
      <td>97.540222</td>
      <td>BROADWAY</td>
      <td>25</td>
      <td>6.0</td>
      <td>WORD</td>
      <td>0.055210</td>
      <td>0.018034</td>
      <td>0.768192</td>
      <td>0.295295</td>
    </tr>
    <tr>
      <th>26</th>
      <td>89.723869</td>
      <td>NEW</td>
      <td>27</td>
      <td>7.0</td>
      <td>WORD</td>
      <td>0.033758</td>
      <td>0.019019</td>
      <td>0.587397</td>
      <td>0.379379</td>
    </tr>
    <tr>
      <th>27</th>
      <td>92.452881</td>
      <td>YORK</td>
      <td>28</td>
      <td>7.0</td>
      <td>WORD</td>
      <td>0.035273</td>
      <td>0.020034</td>
      <td>0.618905</td>
      <td>0.382382</td>
    </tr>
    <tr>
      <th>29</th>
      <td>92.044113</td>
      <td>CITY</td>
      <td>29</td>
      <td>7.0</td>
      <td>WORD</td>
      <td>0.027007</td>
      <td>0.016016</td>
      <td>0.655664</td>
      <td>0.389389</td>
    </tr>
    <tr>
      <th>28</th>
      <td>95.421768</td>
      <td>food</td>
      <td>26</td>
      <td>7.0</td>
      <td>WORD</td>
      <td>0.033758</td>
      <td>0.024024</td>
      <td>0.555889</td>
      <td>0.392392</td>
    </tr>
    <tr>
      <th>33</th>
      <td>96.425499</td>
      <td>WINE</td>
      <td>33</td>
      <td>8.0</td>
      <td>WORD</td>
      <td>0.043511</td>
      <td>0.022022</td>
      <td>0.592648</td>
      <td>0.398398</td>
    </tr>
    <tr>
      <th>31</th>
      <td>87.556793</td>
      <td>LIon</td>
      <td>31</td>
      <td>8.0</td>
      <td>WORD</td>
      <td>0.041260</td>
      <td>0.030030</td>
      <td>0.336084</td>
      <td>0.400400</td>
    </tr>
    <tr>
      <th>32</th>
      <td>90.025482</td>
      <td>KING</td>
      <td>32</td>
      <td>8.0</td>
      <td>WORD</td>
      <td>0.045022</td>
      <td>0.033042</td>
      <td>0.377344</td>
      <td>0.400400</td>
    </tr>
    <tr>
      <th>34</th>
      <td>96.632484</td>
      <td>FOOD</td>
      <td>35</td>
      <td>8.0</td>
      <td>WORD</td>
      <td>0.043522</td>
      <td>0.021034</td>
      <td>0.645911</td>
      <td>0.402402</td>
    </tr>
    <tr>
      <th>30</th>
      <td>98.496071</td>
      <td>THE</td>
      <td>30</td>
      <td>8.0</td>
      <td>WORD</td>
      <td>0.031508</td>
      <td>0.023023</td>
      <td>0.303826</td>
      <td>0.403403</td>
    </tr>
    <tr>
      <th>36</th>
      <td>96.938141</td>
      <td>FESTIVALS</td>
      <td>34</td>
      <td>8.0</td>
      <td>WORD</td>
      <td>0.090028</td>
      <td>0.021034</td>
      <td>0.596399</td>
      <td>0.419419</td>
    </tr>
    <tr>
      <th>35</th>
      <td>71.623650</td>
      <td>EME</td>
      <td>36</td>
      <td>9.0</td>
      <td>WORD</td>
      <td>0.029257</td>
      <td>0.027027</td>
      <td>0.450113</td>
      <td>0.426426</td>
    </tr>
    <tr>
      <th>37</th>
      <td>88.608627</td>
      <td>Oct.9-12</td>
      <td>37</td>
      <td>9.0</td>
      <td>WORD</td>
      <td>0.036773</td>
      <td>0.016016</td>
      <td>0.553638</td>
      <td>0.437437</td>
    </tr>
    <tr>
      <th>38</th>
      <td>91.010559</td>
      <td>SALE</td>
      <td>38</td>
      <td>9.0</td>
      <td>WORD</td>
      <td>0.023788</td>
      <td>0.018158</td>
      <td>0.735934</td>
      <td>0.452452</td>
    </tr>
    <tr>
      <th>39</th>
      <td>80.209969</td>
      <td>02</td>
      <td>39</td>
      <td>10.0</td>
      <td>WORD</td>
      <td>0.024027</td>
      <td>0.021034</td>
      <td>0.077269</td>
      <td>0.488488</td>
    </tr>
    <tr>
      <th>40</th>
      <td>85.682373</td>
      <td>9214'',</td>
      <td>40</td>
      <td>11.0</td>
      <td>WORD</td>
      <td>0.112688</td>
      <td>0.028068</td>
      <td>0.762191</td>
      <td>0.600601</td>
    </tr>
    <tr>
      <th>41</th>
      <td>97.959709</td>
      <td>TAXI</td>
      <td>42</td>
      <td>12.0</td>
      <td>WORD</td>
      <td>0.104583</td>
      <td>0.052101</td>
      <td>0.488372</td>
      <td>0.716717</td>
    </tr>
    <tr>
      <th>42</th>
      <td>96.415970</td>
      <td>NYC</td>
      <td>41</td>
      <td>12.0</td>
      <td>WORD</td>
      <td>0.066138</td>
      <td>0.036067</td>
      <td>0.414104</td>
      <td>0.736737</td>
    </tr>
  </tbody>
</table>
</div>



### Detect Celebs
Traffic analytics may also involve detecting VIP movement to divert traffic or monitor security events. Detecting VIP in a scene starts with facial recognition. Our function ``detect_celebs`` works as well with political figures as it will with movie celebrities.


```python
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
```


```python
show_image(image_bucket, 'images/world-leaders.jpg', 1024)
```




<img src="https://s3.amazonaws.com/open-data-analytics-taxi-trips/images/world-leaders.jpg" width="1024"/>




```python
detect_celebs(image_bucket, 'images/world-leaders.jpg', sort_column='Left')
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Id</th>
      <th>MatchConfidence</th>
      <th>Name</th>
      <th>Urls</th>
      <th>Width</th>
      <th>Height</th>
      <th>Left</th>
      <th>Top</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>3</th>
      <td>4Ev8IX1</td>
      <td>100.0</td>
      <td>Chulabhorn</td>
      <td>[]</td>
      <td>0.020202</td>
      <td>0.038973</td>
      <td>0.015152</td>
      <td>0.424905</td>
    </tr>
    <tr>
      <th>5</th>
      <td>3J795K</td>
      <td>100.0</td>
      <td>Manmohan Singh</td>
      <td>[]</td>
      <td>0.018687</td>
      <td>0.035171</td>
      <td>0.131313</td>
      <td>0.420152</td>
    </tr>
    <tr>
      <th>25</th>
      <td>f0JR5e</td>
      <td>90.0</td>
      <td>Mahinda Rajapaksa</td>
      <td>[]</td>
      <td>0.016162</td>
      <td>0.030418</td>
      <td>0.145960</td>
      <td>0.319392</td>
    </tr>
    <tr>
      <th>30</th>
      <td>3n7tl2O</td>
      <td>88.0</td>
      <td>Killah Priest</td>
      <td>[www.imdb.com/name/nm0697334]</td>
      <td>0.014646</td>
      <td>0.027567</td>
      <td>0.162121</td>
      <td>0.290875</td>
    </tr>
    <tr>
      <th>12</th>
      <td>2gC0Tc0e</td>
      <td>100.0</td>
      <td>Rosen Plevneliev</td>
      <td>[]</td>
      <td>0.018182</td>
      <td>0.034221</td>
      <td>0.179293</td>
      <td>0.367871</td>
    </tr>
    <tr>
      <th>19</th>
      <td>3LR2lb6j</td>
      <td>56.0</td>
      <td>Jerry Harrison</td>
      <td>[]</td>
      <td>0.017172</td>
      <td>0.032319</td>
      <td>0.227273</td>
      <td>0.330798</td>
    </tr>
    <tr>
      <th>1</th>
      <td>4hD40O</td>
      <td>100.0</td>
      <td>Thomas Boni Yayi</td>
      <td>[]</td>
      <td>0.021717</td>
      <td>0.040875</td>
      <td>0.236364</td>
      <td>0.399240</td>
    </tr>
    <tr>
      <th>22</th>
      <td>2F5LV4</td>
      <td>63.0</td>
      <td>Irwansyah</td>
      <td>[www.imdb.com/name/nm2679097]</td>
      <td>0.016667</td>
      <td>0.031369</td>
      <td>0.274747</td>
      <td>0.340304</td>
    </tr>
    <tr>
      <th>8</th>
      <td>3hk2qj5G</td>
      <td>98.0</td>
      <td>Cristina Fernández de Kirchner</td>
      <td>[www.imdb.com/name/nm3231417]</td>
      <td>0.018687</td>
      <td>0.035171</td>
      <td>0.278283</td>
      <td>0.414449</td>
    </tr>
    <tr>
      <th>13</th>
      <td>2sN1oC8s</td>
      <td>100.0</td>
      <td>Jorge Carlos Fonseca</td>
      <td>[]</td>
      <td>0.018182</td>
      <td>0.034221</td>
      <td>0.280808</td>
      <td>0.370722</td>
    </tr>
    <tr>
      <th>9</th>
      <td>3Ns4kC2b</td>
      <td>100.0</td>
      <td>Sebastián Piñera</td>
      <td>[]</td>
      <td>0.018687</td>
      <td>0.035171</td>
      <td>0.318687</td>
      <td>0.374525</td>
    </tr>
    <tr>
      <th>15</th>
      <td>1qy7Yt8D</td>
      <td>100.0</td>
      <td>Gurbanguly Berdimuhamedow</td>
      <td>[]</td>
      <td>0.018182</td>
      <td>0.034221</td>
      <td>0.334848</td>
      <td>0.317490</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1eA7EJ2W</td>
      <td>63.0</td>
      <td>Salim Durani</td>
      <td>[]</td>
      <td>0.019192</td>
      <td>0.036122</td>
      <td>0.418687</td>
      <td>0.331749</td>
    </tr>
    <tr>
      <th>20</th>
      <td>2vr4uV3M</td>
      <td>95.0</td>
      <td>Albert II, Prince of Monaco</td>
      <td>[]</td>
      <td>0.017172</td>
      <td>0.032319</td>
      <td>0.463636</td>
      <td>0.332700</td>
    </tr>
    <tr>
      <th>29</th>
      <td>4pv6OP8</td>
      <td>90.0</td>
      <td>Nick Clegg</td>
      <td>[www.imdb.com/name/nm2200958]</td>
      <td>0.015152</td>
      <td>0.028517</td>
      <td>0.465152</td>
      <td>0.255703</td>
    </tr>
    <tr>
      <th>7</th>
      <td>pL8KD9X</td>
      <td>100.0</td>
      <td>Denis Sassou Nguesso</td>
      <td>[]</td>
      <td>0.018687</td>
      <td>0.035171</td>
      <td>0.472727</td>
      <td>0.368821</td>
    </tr>
    <tr>
      <th>0</th>
      <td>46JZ2c</td>
      <td>97.0</td>
      <td>Ban Ki-moon</td>
      <td>[www.imdb.com/name/nm2559634]</td>
      <td>0.022727</td>
      <td>0.042776</td>
      <td>0.526768</td>
      <td>0.402091</td>
    </tr>
    <tr>
      <th>27</th>
      <td>2yG8Fe4x</td>
      <td>79.0</td>
      <td>Mem Fox</td>
      <td>[]</td>
      <td>0.015152</td>
      <td>0.028517</td>
      <td>0.607071</td>
      <td>0.351711</td>
    </tr>
    <tr>
      <th>18</th>
      <td>2nk8Bd0</td>
      <td>58.0</td>
      <td>Ali Bongo Ondimba</td>
      <td>[]</td>
      <td>0.017172</td>
      <td>0.032319</td>
      <td>0.612121</td>
      <td>0.381179</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2aE2DV3K</td>
      <td>100.0</td>
      <td>Susilo Bambang Yudhoyono</td>
      <td>[www.imdb.com/name/nm2670444]</td>
      <td>0.020707</td>
      <td>0.038973</td>
      <td>0.626263</td>
      <td>0.403042</td>
    </tr>
    <tr>
      <th>17</th>
      <td>3m4lC0</td>
      <td>82.0</td>
      <td>Uhuru Kenyatta</td>
      <td>[www.imdb.com/name/nm6045979]</td>
      <td>0.017172</td>
      <td>0.032319</td>
      <td>0.650505</td>
      <td>0.343156</td>
    </tr>
    <tr>
      <th>28</th>
      <td>K8hL4i</td>
      <td>67.0</td>
      <td>Erkki Tuomioja</td>
      <td>[]</td>
      <td>0.015152</td>
      <td>0.028517</td>
      <td>0.657071</td>
      <td>0.280418</td>
    </tr>
    <tr>
      <th>26</th>
      <td>2KJ7KM8e</td>
      <td>100.0</td>
      <td>Isatou Njie-Saidy</td>
      <td>[]</td>
      <td>0.015657</td>
      <td>0.029468</td>
      <td>0.666162</td>
      <td>0.396388</td>
    </tr>
    <tr>
      <th>14</th>
      <td>aU4fU4</td>
      <td>100.0</td>
      <td>Laura Chinchilla</td>
      <td>[]</td>
      <td>0.018182</td>
      <td>0.034221</td>
      <td>0.679798</td>
      <td>0.429658</td>
    </tr>
    <tr>
      <th>16</th>
      <td>2DM2OT1F</td>
      <td>91.0</td>
      <td>Alpha Condé</td>
      <td>[]</td>
      <td>0.017677</td>
      <td>0.033270</td>
      <td>0.708586</td>
      <td>0.369772</td>
    </tr>
    <tr>
      <th>11</th>
      <td>4eh5t9f</td>
      <td>99.0</td>
      <td>Helle Thorning-Schmidt</td>
      <td>[www.imdb.com/name/nm1525284]</td>
      <td>0.018182</td>
      <td>0.034221</td>
      <td>0.723232</td>
      <td>0.399240</td>
    </tr>
    <tr>
      <th>21</th>
      <td>Em8cA8q</td>
      <td>70.0</td>
      <td>Ollanta Humala</td>
      <td>[]</td>
      <td>0.017172</td>
      <td>0.032319</td>
      <td>0.766667</td>
      <td>0.355513</td>
    </tr>
    <tr>
      <th>24</th>
      <td>4FT4On6a</td>
      <td>94.0</td>
      <td>Mariano Rajoy</td>
      <td>[www.imdb.com/name/nm1775577]</td>
      <td>0.016162</td>
      <td>0.030418</td>
      <td>0.786869</td>
      <td>0.282319</td>
    </tr>
    <tr>
      <th>23</th>
      <td>1oa5Af1</td>
      <td>73.0</td>
      <td>James Van Praagh</td>
      <td>[www.imdb.com/name/nm1070530]</td>
      <td>0.016667</td>
      <td>0.031369</td>
      <td>0.806061</td>
      <td>0.378327</td>
    </tr>
    <tr>
      <th>10</th>
      <td>47mP82</td>
      <td>82.0</td>
      <td>János Áder</td>
      <td>[]</td>
      <td>0.018182</td>
      <td>0.034221</td>
      <td>0.848485</td>
      <td>0.365970</td>
    </tr>
    <tr>
      <th>6</th>
      <td>16BU2ey</td>
      <td>99.0</td>
      <td>José Manuel Barroso</td>
      <td>[]</td>
      <td>0.018687</td>
      <td>0.035171</td>
      <td>0.960606</td>
      <td>0.408745</td>
    </tr>
  </tbody>
</table>
</div>



### Comprehend Syntax
It is possible that many data sources represent natural language and free text. Understand structure and semantics from this unstructured text can help further our open data analytics use cases.

Let us assume we are processing traffic updates for structured data so we can take appropriate actions. First step in understanding natural language is to break it up into grammaticaly syntax. Nouns like "today" can tell about a particular event like when is the event occuring. Adjectives like "snowing" and "windy" tell what is happening at that moment in time. 


```python
comprehend = boto3.client('comprehend', 'us-east-1')

traffic_update = """
It is snowing and windy today in New York. The temperature is 50 degrees Fahrenheit. 
The traffic is slow 10 mph with several jams along the I-86.
"""
```


```python
def comprehend_syntax(text): 
    response = comprehend.detect_syntax(Text=text, LanguageCode='en')
    df = pd.read_json(io.StringIO(json.dumps(response['SyntaxTokens'])))
    df['Tag'] = df['PartOfSpeech'].apply(lambda x: x['Tag'])
    df['Score'] = df['PartOfSpeech'].apply(lambda x: x['Score'])
    df = df.drop(columns=['PartOfSpeech'])
    return df
```


```python
comprehend_syntax(traffic_update)
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>BeginOffset</th>
      <th>EndOffset</th>
      <th>Text</th>
      <th>TokenId</th>
      <th>Tag</th>
      <th>Score</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>3</td>
      <td>It</td>
      <td>1</td>
      <td>PRON</td>
      <td>0.999971</td>
    </tr>
    <tr>
      <th>1</th>
      <td>4</td>
      <td>6</td>
      <td>is</td>
      <td>2</td>
      <td>VERB</td>
      <td>0.557677</td>
    </tr>
    <tr>
      <th>2</th>
      <td>7</td>
      <td>14</td>
      <td>snowing</td>
      <td>3</td>
      <td>ADJ</td>
      <td>0.687805</td>
    </tr>
    <tr>
      <th>3</th>
      <td>15</td>
      <td>18</td>
      <td>and</td>
      <td>4</td>
      <td>CONJ</td>
      <td>0.999998</td>
    </tr>
    <tr>
      <th>4</th>
      <td>19</td>
      <td>24</td>
      <td>windy</td>
      <td>5</td>
      <td>ADJ</td>
      <td>0.994336</td>
    </tr>
    <tr>
      <th>5</th>
      <td>25</td>
      <td>30</td>
      <td>today</td>
      <td>6</td>
      <td>NOUN</td>
      <td>0.999980</td>
    </tr>
    <tr>
      <th>6</th>
      <td>31</td>
      <td>33</td>
      <td>in</td>
      <td>7</td>
      <td>ADP</td>
      <td>0.999924</td>
    </tr>
    <tr>
      <th>7</th>
      <td>34</td>
      <td>37</td>
      <td>New</td>
      <td>8</td>
      <td>PROPN</td>
      <td>0.999351</td>
    </tr>
    <tr>
      <th>8</th>
      <td>38</td>
      <td>42</td>
      <td>York</td>
      <td>9</td>
      <td>PROPN</td>
      <td>0.998399</td>
    </tr>
    <tr>
      <th>9</th>
      <td>42</td>
      <td>43</td>
      <td>.</td>
      <td>10</td>
      <td>PUNCT</td>
      <td>0.999998</td>
    </tr>
    <tr>
      <th>10</th>
      <td>44</td>
      <td>47</td>
      <td>The</td>
      <td>11</td>
      <td>DET</td>
      <td>0.999979</td>
    </tr>
    <tr>
      <th>11</th>
      <td>48</td>
      <td>59</td>
      <td>temperature</td>
      <td>12</td>
      <td>NOUN</td>
      <td>0.999760</td>
    </tr>
    <tr>
      <th>12</th>
      <td>60</td>
      <td>62</td>
      <td>is</td>
      <td>13</td>
      <td>VERB</td>
      <td>0.998011</td>
    </tr>
    <tr>
      <th>13</th>
      <td>63</td>
      <td>65</td>
      <td>50</td>
      <td>14</td>
      <td>NUM</td>
      <td>0.999716</td>
    </tr>
    <tr>
      <th>14</th>
      <td>66</td>
      <td>73</td>
      <td>degrees</td>
      <td>15</td>
      <td>NOUN</td>
      <td>0.999700</td>
    </tr>
    <tr>
      <th>15</th>
      <td>74</td>
      <td>84</td>
      <td>Fahrenheit</td>
      <td>16</td>
      <td>PROPN</td>
      <td>0.950743</td>
    </tr>
    <tr>
      <th>16</th>
      <td>84</td>
      <td>85</td>
      <td>.</td>
      <td>17</td>
      <td>PUNCT</td>
      <td>0.999994</td>
    </tr>
    <tr>
      <th>17</th>
      <td>87</td>
      <td>90</td>
      <td>The</td>
      <td>18</td>
      <td>DET</td>
      <td>0.999975</td>
    </tr>
    <tr>
      <th>18</th>
      <td>91</td>
      <td>98</td>
      <td>traffic</td>
      <td>19</td>
      <td>NOUN</td>
      <td>0.999450</td>
    </tr>
    <tr>
      <th>19</th>
      <td>99</td>
      <td>101</td>
      <td>is</td>
      <td>20</td>
      <td>VERB</td>
      <td>0.965014</td>
    </tr>
    <tr>
      <th>20</th>
      <td>102</td>
      <td>106</td>
      <td>slow</td>
      <td>21</td>
      <td>ADJ</td>
      <td>0.815718</td>
    </tr>
    <tr>
      <th>21</th>
      <td>107</td>
      <td>109</td>
      <td>10</td>
      <td>22</td>
      <td>NUM</td>
      <td>0.999991</td>
    </tr>
    <tr>
      <th>22</th>
      <td>110</td>
      <td>113</td>
      <td>mph</td>
      <td>23</td>
      <td>NOUN</td>
      <td>0.988531</td>
    </tr>
    <tr>
      <th>23</th>
      <td>114</td>
      <td>118</td>
      <td>with</td>
      <td>24</td>
      <td>ADP</td>
      <td>0.973397</td>
    </tr>
    <tr>
      <th>24</th>
      <td>119</td>
      <td>126</td>
      <td>several</td>
      <td>25</td>
      <td>ADJ</td>
      <td>0.999647</td>
    </tr>
    <tr>
      <th>25</th>
      <td>127</td>
      <td>131</td>
      <td>jams</td>
      <td>26</td>
      <td>NOUN</td>
      <td>0.999936</td>
    </tr>
    <tr>
      <th>26</th>
      <td>132</td>
      <td>137</td>
      <td>along</td>
      <td>27</td>
      <td>ADP</td>
      <td>0.997718</td>
    </tr>
    <tr>
      <th>27</th>
      <td>138</td>
      <td>141</td>
      <td>the</td>
      <td>28</td>
      <td>DET</td>
      <td>0.999960</td>
    </tr>
    <tr>
      <th>28</th>
      <td>142</td>
      <td>143</td>
      <td>I</td>
      <td>29</td>
      <td>PROPN</td>
      <td>0.745183</td>
    </tr>
    <tr>
      <th>29</th>
      <td>143</td>
      <td>144</td>
      <td>-</td>
      <td>30</td>
      <td>PUNCT</td>
      <td>0.999858</td>
    </tr>
    <tr>
      <th>30</th>
      <td>144</td>
      <td>146</td>
      <td>86</td>
      <td>31</td>
      <td>PROPN</td>
      <td>0.684016</td>
    </tr>
    <tr>
      <th>31</th>
      <td>146</td>
      <td>147</td>
      <td>.</td>
      <td>32</td>
      <td>PUNCT</td>
      <td>0.999985</td>
    </tr>
  </tbody>
</table>
</div>



### Comprehend Entities
More insights can be derived by doing entity extraction from the natural langauage. These entities can be date, location, quantity, among others. Just few of the entities can tell a structured story to a program.


```python
def comprehend_entities(text):
    response = comprehend.detect_entities(Text=text, LanguageCode='en')
    df = pd.read_json(io.StringIO(json.dumps(response['Entities'])))
    return df
```


```python
comprehend_entities(traffic_update)
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>BeginOffset</th>
      <th>EndOffset</th>
      <th>Score</th>
      <th>Text</th>
      <th>Type</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>25</td>
      <td>30</td>
      <td>0.839589</td>
      <td>today</td>
      <td>DATE</td>
    </tr>
    <tr>
      <th>1</th>
      <td>34</td>
      <td>42</td>
      <td>0.998423</td>
      <td>New York</td>
      <td>LOCATION</td>
    </tr>
    <tr>
      <th>2</th>
      <td>63</td>
      <td>84</td>
      <td>0.984396</td>
      <td>50 degrees Fahrenheit</td>
      <td>QUANTITY</td>
    </tr>
    <tr>
      <th>3</th>
      <td>107</td>
      <td>113</td>
      <td>0.992498</td>
      <td>10 mph</td>
      <td>QUANTITY</td>
    </tr>
    <tr>
      <th>4</th>
      <td>142</td>
      <td>146</td>
      <td>0.990993</td>
      <td>I-86</td>
      <td>LOCATION</td>
    </tr>
  </tbody>
</table>
</div>



### Comprehend Phrases
Analysis of phrases within narutal language text complements the other two methods for a program to better route the actions based on derived structure of the event.


```python
def comprehend_phrases(text):
    response = comprehend.detect_key_phrases(Text=text, LanguageCode='en')
    df = pd.read_json(io.StringIO(json.dumps(response['KeyPhrases'])))
    return df
```


```python
comprehend_phrases(traffic_update)
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>BeginOffset</th>
      <th>EndOffset</th>
      <th>Score</th>
      <th>Text</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>25</td>
      <td>30</td>
      <td>0.988285</td>
      <td>today</td>
    </tr>
    <tr>
      <th>1</th>
      <td>34</td>
      <td>42</td>
      <td>0.997397</td>
      <td>New York</td>
    </tr>
    <tr>
      <th>2</th>
      <td>44</td>
      <td>59</td>
      <td>0.999752</td>
      <td>The temperature</td>
    </tr>
    <tr>
      <th>3</th>
      <td>63</td>
      <td>73</td>
      <td>0.789843</td>
      <td>50 degrees</td>
    </tr>
    <tr>
      <th>4</th>
      <td>87</td>
      <td>98</td>
      <td>0.999843</td>
      <td>The traffic</td>
    </tr>
    <tr>
      <th>5</th>
      <td>107</td>
      <td>113</td>
      <td>0.924737</td>
      <td>10 mph</td>
    </tr>
    <tr>
      <th>6</th>
      <td>119</td>
      <td>131</td>
      <td>0.998428</td>
      <td>several jams</td>
    </tr>
    <tr>
      <th>7</th>
      <td>138</td>
      <td>146</td>
      <td>0.997108</td>
      <td>the I-86</td>
    </tr>
  </tbody>
</table>
</div>



### Comprehend Sentiment
Sentiment analysis is common for social media user generated content. Sentiment can give us signals on the users' mood when publishing such social data.


```python
def comprehend_sentiment(text):
    response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
    return response['SentimentScore']
```


```python
comprehend_sentiment(traffic_update)
```




    {'Positive': 0.04090394824743271,
     'Negative': 0.3745909333229065,
     'Neutral': 0.5641733407974243,
     'Mixed': 0.020331736654043198}



### Change Log

This section captures changes and updates to this notebook across releases.

#### Usability and sorting for text and face detection - Release 3 MAY 2019
Functions ``image_text`` and ``detect_celeb`` can now sort results based on a column name. Function ``image_text`` can optionally show results without parent-child relations.

Usability update for ``comprehend_syntax`` function to split ``part of speech`` dictionary value into separate Tag and Score columns.

#### Launch - Release 30 APR 2019
This is the launch release which builds the AWS Open Data Analytics API for using AWS AI services to analyze public data.


---
#### Using AI Services for Analyzing Public Data
by Manav Sehgal | on APR 30 2019

