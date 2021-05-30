
## Optimizing data for analysis with Amazon Athena and AWS Glue

We will continue our open data analytics workflow starting with the AWS Console then moving to using the notebook. Using [AWS Glue](https://aws.amazon.com/glue/) we can automate creating a metadata catalog based on flat files stored on Amazon S3. Glue is a fully managed extract, transform, and load (ETL) service that makes it easy for customers to prepare and load their data for analytics. You can create and run an ETL job with a few clicks in the AWS Management Console. You simply point AWS Glue to your data stored on AWS, and AWS Glue discovers your data and stores the associated metadata (e.g. table definition and schema) in the AWS Glue Data Catalog. Once cataloged, your data is immediately searchable, queryable, and available for ETL.

### Glue Data Catalog

We have sourced the open dataset from the [Registry of Open Data on AWS](https://registry.opendata.aws/). We also stored the data on S3. Now we are ready to extract, transform, and load the data for analytics. We will use AWS Glue service to do this. First step is to create a logical database entry in the data catalog. Note that we are not creating a physical database which requires resources. This is just a metadata placeholder for the flat file we copied into S3.

> When creating the data catalog name try choosing a name without hyphens and few characters long. This will make SQL queries more readable and also avoid certain errors when running these queries.

![Glue Data Catalog](https://s3.amazonaws.com/cloudstory/notebooks-media/glue-data-catalog.png)

We can also setup the notebook for accessing AWS Glue service using the ``Boto3`` Python SDK. The ``pandas`` and ``IPython`` dependencies are imported for output formatting purposes only. We also import ``numpy`` a popular statistical analysis library. Charts and visualizations will be supported by ``seaborn`` and ``matplotlib`` libraries. To access the Glue service API we create a Glue client. 


```python
import boto3
import pandas as pd
import numpy as np
from IPython.display import display, Markdown
import seaborn as sns
%matplotlib inline
import matplotlib.pyplot as plt
```


```python
glue = boto3.client('glue')
s3 = boto3.client('s3')
```

### List Glue Databases
We will recreate the AWS Console GUI experience using SDK calls by creating the ``list_glue_databases`` function. We simply get the data catalogs in one statement and iterate over the results in the next one.


```python
def list_glue_databases():
    glue_database = glue.get_databases()

    for db in glue_database['DatabaseList']:
        print(db['Name'])
```


```python
list_glue_databases()
```

    default
    odoc
    sampledb
    taxicatalog


### Glue Crawler
Next, we create a logical table using Glue crawler. This is again just table metadata definition while the actual data is still stored only in the flat file on S3. For this notebook we will define and run the default Glue Crawler to extract and load the metadata schema from our flat file. This requires selection of a data store which is S3 in this case, defining an IAM role for access from Glue to S3, selecting a schedule for the crawler to run repeatedly if required, and output destination of the crawler results. 

> Please ensure that the flat file is stored on S3 within its own folder and you point at the folder when picking the data source during crawler definition. If you point directly to a flat file when running the crawler, it may return zero results when querying using Amazon Athena.

Glue will pick up folder name for the logical table name. Keeping our data source files in a folder has the added advantage of incremntally updating the folder with updates to the data with more files or updating the original file. Glue will pick up these changes based on crawler run schedule.

![Glue Crawler](https://s3.amazonaws.com/cloudstory/notebooks-media/glue-crawler.png)

### Glue Table Metadata
This results in extraction of table metadata stored within our data catalog. The schema with data types is extracted and stored in Glue Data Catalog. Note that the default Glue Crawler understands well-formed CSV files with first row as comma-separated list of column names, and next set of rows representing ordered data records. The Glue Crawler automatically guesses data types based on the contents of the flat file.

![Table Metadata](https://s3.amazonaws.com/cloudstory/notebooks-media/table-metadata.png)

### Transform Data Using Athena

Transforming big data in notebook environment is not viable. Instead we can use Amazon Athena for large data transforms and bring the results back into our notebook.

![Athena Transform Data](https://s3.amazonaws.com/cloudstory/notebooks-media/athena-transform-data.png)

We will use following query to create a well formed table transformed from our original table. Note that we specify the output location so that Athena defined WorkGroup location is not used by default. We also specify the format as ``TEXTFILE`` otherwise default ``PARQUET`` format is used which may generate errors when sampling this data.

```SQL
CREATE TABLE 
IF NOT EXISTS "taxicatalog"."many_trips_well_formed" 
WITH (
    external_location = 's3://open-data-analytics-taxi-trips/many-trips-well-formed/',
    format = 'TEXTFILE',
    field_delimiter = ','
)
AS SELECT vendorid AS vendor,
         passenger_count AS passengers,
         trip_distance AS distance,
         ratecodeid AS rate,
         pulocationid AS pick_location,
         dolocationid AS drop_location,
         payment_type AS payment_type,
         fare_amount AS fare,
         extra AS extra_fare,
         mta_tax AS tax,
         tip_amount AS tip,
         tolls_amount AS toll,
         improvement_surcharge AS surcharge,
         total_amount AS total_fare,
         tpep_pickup_datetime AS pick_when,
         tpep_dropoff_datetime AS drop_when
FROM "taxicatalog"."many_trips";
```


### List Glue Tables
In the spirit of AWS Open Data Analytics API we will recreate the AWS Console feature which lists the tables and displays the metadata within one single reusable function. We get the list of table metadata stored within our data catalog by passing the ``database`` parameter. Next we iterate over each table object and display the name, source data file, number of records (estimate), average record size, data size in MB, and the name of the crawler used to extract the table metadata. We also display the list of column names and data types extracted as schema from the flat file stored on S3.


```python
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
```


```python
list_glue_tables('taxicatalog', verbose=False)
```


**Table: many_trips**



Location: s3://open-data-analytics-taxi-trips/many-trips/



Created by: AWS-Crawler



**Table: many_trips_well_formed**



Location: s3://open-data-analytics-taxi-trips/many-trips-well-formed



Created by: manav



```python
athena = boto3.client('athena')
```

### Athena Query
Our next action is to bring the data created within Athena into the notebook environment using a ``pandas`` DataFrame. This can be done using the ``athena_query`` function which calls the Amazon Athena API to execute a query and store the output within a bucket and folder. This output is then read by a DataFrame which is returned by the function.


```python
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
```

To explore the data within Athena we will query returning thousand random samples.


```python
bucket = 'open-data-analytics-taxi-trips'
folder = 'queries'
query = 'SELECT * FROM "taxicatalog"."many_trips_well_formed" TABLESAMPLE BERNOULLI(100) LIMIT 1000;'

df = athena_query(query, bucket, folder)
df.head()
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>vendor</th>
      <th>passengers</th>
      <th>distance</th>
      <th>rate</th>
      <th>pick_location</th>
      <th>drop_location</th>
      <th>payment_type</th>
      <th>fare</th>
      <th>extra_fare</th>
      <th>tax</th>
      <th>tip</th>
      <th>toll</th>
      <th>surcharge</th>
      <th>total_fare</th>
      <th>pick_when</th>
      <th>drop_when</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2</td>
      <td>1</td>
      <td>1.25</td>
      <td>1</td>
      <td>237</td>
      <td>236</td>
      <td>1</td>
      <td>9.0</td>
      <td>0.0</td>
      <td>0.5</td>
      <td>0.00</td>
      <td>0.0</td>
      <td>0.3</td>
      <td>9.80</td>
      <td>2018-06-06 10:43:34</td>
      <td>2018-06-06 10:54:58</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>1</td>
      <td>1.20</td>
      <td>1</td>
      <td>158</td>
      <td>90</td>
      <td>2</td>
      <td>7.5</td>
      <td>0.0</td>
      <td>0.5</td>
      <td>0.00</td>
      <td>0.0</td>
      <td>0.3</td>
      <td>8.30</td>
      <td>2018-06-06 10:06:22</td>
      <td>2018-06-06 10:15:21</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>1</td>
      <td>3.30</td>
      <td>1</td>
      <td>234</td>
      <td>236</td>
      <td>1</td>
      <td>17.0</td>
      <td>0.0</td>
      <td>0.5</td>
      <td>3.55</td>
      <td>0.0</td>
      <td>0.3</td>
      <td>21.35</td>
      <td>2018-06-06 10:17:20</td>
      <td>2018-06-06 10:43:07</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1</td>
      <td>1</td>
      <td>0.90</td>
      <td>1</td>
      <td>236</td>
      <td>140</td>
      <td>1</td>
      <td>7.0</td>
      <td>0.0</td>
      <td>0.5</td>
      <td>1.55</td>
      <td>0.0</td>
      <td>0.3</td>
      <td>9.35</td>
      <td>2018-06-06 10:48:28</td>
      <td>2018-06-06 10:57:08</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1</td>
      <td>1</td>
      <td>1.00</td>
      <td>1</td>
      <td>141</td>
      <td>162</td>
      <td>1</td>
      <td>7.0</td>
      <td>0.0</td>
      <td>0.5</td>
      <td>1.95</td>
      <td>0.0</td>
      <td>0.3</td>
      <td>9.75</td>
      <td>2018-06-06 10:59:28</td>
      <td>2018-06-06 11:08:05</td>
    </tr>
  </tbody>
</table>
</div>



Next we will determine statistical correlation between various features (columns) within the given set of samples (records).


```python
corr = df.corr(method ='spearman')
corr
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>vendor</th>
      <th>passengers</th>
      <th>distance</th>
      <th>rate</th>
      <th>pick_location</th>
      <th>drop_location</th>
      <th>payment_type</th>
      <th>fare</th>
      <th>extra_fare</th>
      <th>tax</th>
      <th>tip</th>
      <th>toll</th>
      <th>surcharge</th>
      <th>total_fare</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>vendor</th>
      <td>1.000000</td>
      <td>0.283619</td>
      <td>0.015401</td>
      <td>0.055897</td>
      <td>-0.024097</td>
      <td>-0.005115</td>
      <td>0.013634</td>
      <td>-0.014083</td>
      <td>NaN</td>
      <td>-0.009308</td>
      <td>-0.024436</td>
      <td>0.025840</td>
      <td>NaN</td>
      <td>-0.015078</td>
    </tr>
    <tr>
      <th>passengers</th>
      <td>0.283619</td>
      <td>1.000000</td>
      <td>0.033053</td>
      <td>0.051624</td>
      <td>-0.021166</td>
      <td>0.003783</td>
      <td>0.020200</td>
      <td>0.035106</td>
      <td>NaN</td>
      <td>-0.022736</td>
      <td>0.008936</td>
      <td>0.003765</td>
      <td>NaN</td>
      <td>0.033289</td>
    </tr>
    <tr>
      <th>distance</th>
      <td>0.015401</td>
      <td>0.033053</td>
      <td>1.000000</td>
      <td>0.119010</td>
      <td>-0.119491</td>
      <td>-0.148011</td>
      <td>-0.068732</td>
      <td>0.917127</td>
      <td>NaN</td>
      <td>-0.080828</td>
      <td>0.389773</td>
      <td>0.401863</td>
      <td>NaN</td>
      <td>0.903529</td>
    </tr>
    <tr>
      <th>rate</th>
      <td>0.055897</td>
      <td>0.051624</td>
      <td>0.119010</td>
      <td>1.000000</td>
      <td>-0.042557</td>
      <td>-0.053956</td>
      <td>-0.007774</td>
      <td>0.185992</td>
      <td>NaN</td>
      <td>-0.501256</td>
      <td>0.083778</td>
      <td>0.246460</td>
      <td>NaN</td>
      <td>0.184445</td>
    </tr>
    <tr>
      <th>pick_location</th>
      <td>-0.024097</td>
      <td>-0.021166</td>
      <td>-0.119491</td>
      <td>-0.042557</td>
      <td>1.000000</td>
      <td>0.150656</td>
      <td>-0.009998</td>
      <td>-0.129692</td>
      <td>NaN</td>
      <td>0.010869</td>
      <td>-0.028087</td>
      <td>-0.153488</td>
      <td>NaN</td>
      <td>-0.127936</td>
    </tr>
    <tr>
      <th>drop_location</th>
      <td>-0.005115</td>
      <td>0.003783</td>
      <td>-0.148011</td>
      <td>-0.053956</td>
      <td>0.150656</td>
      <td>1.000000</td>
      <td>0.003079</td>
      <td>-0.162211</td>
      <td>NaN</td>
      <td>0.090225</td>
      <td>-0.042135</td>
      <td>-0.087721</td>
      <td>NaN</td>
      <td>-0.154017</td>
    </tr>
    <tr>
      <th>payment_type</th>
      <td>0.013634</td>
      <td>0.020200</td>
      <td>-0.068732</td>
      <td>-0.007774</td>
      <td>-0.009998</td>
      <td>0.003079</td>
      <td>1.000000</td>
      <td>-0.073051</td>
      <td>NaN</td>
      <td>-0.015087</td>
      <td>-0.776507</td>
      <td>-0.068458</td>
      <td>NaN</td>
      <td>-0.212893</td>
    </tr>
    <tr>
      <th>fare</th>
      <td>-0.014083</td>
      <td>0.035106</td>
      <td>0.917127</td>
      <td>0.185992</td>
      <td>-0.129692</td>
      <td>-0.162211</td>
      <td>-0.073051</td>
      <td>1.000000</td>
      <td>NaN</td>
      <td>-0.091508</td>
      <td>0.425216</td>
      <td>0.395950</td>
      <td>NaN</td>
      <td>0.983444</td>
    </tr>
    <tr>
      <th>extra_fare</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>tax</th>
      <td>-0.009308</td>
      <td>-0.022736</td>
      <td>-0.080828</td>
      <td>-0.501256</td>
      <td>0.010869</td>
      <td>0.090225</td>
      <td>-0.015087</td>
      <td>-0.091508</td>
      <td>NaN</td>
      <td>1.000000</td>
      <td>0.012988</td>
      <td>-0.148891</td>
      <td>NaN</td>
      <td>-0.089695</td>
    </tr>
    <tr>
      <th>tip</th>
      <td>-0.024436</td>
      <td>0.008936</td>
      <td>0.389773</td>
      <td>0.083778</td>
      <td>-0.028087</td>
      <td>-0.042135</td>
      <td>-0.776507</td>
      <td>0.425216</td>
      <td>NaN</td>
      <td>0.012988</td>
      <td>1.000000</td>
      <td>0.267483</td>
      <td>NaN</td>
      <td>0.555170</td>
    </tr>
    <tr>
      <th>toll</th>
      <td>0.025840</td>
      <td>0.003765</td>
      <td>0.401863</td>
      <td>0.246460</td>
      <td>-0.153488</td>
      <td>-0.087721</td>
      <td>-0.068458</td>
      <td>0.395950</td>
      <td>NaN</td>
      <td>-0.148891</td>
      <td>0.267483</td>
      <td>1.000000</td>
      <td>NaN</td>
      <td>0.403146</td>
    </tr>
    <tr>
      <th>surcharge</th>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>total_fare</th>
      <td>-0.015078</td>
      <td>0.033289</td>
      <td>0.903529</td>
      <td>0.184445</td>
      <td>-0.127936</td>
      <td>-0.154017</td>
      <td>-0.212893</td>
      <td>0.983444</td>
      <td>NaN</td>
      <td>-0.089695</td>
      <td>0.555170</td>
      <td>0.403146</td>
      <td>NaN</td>
      <td>1.000000</td>
    </tr>
  </tbody>
</table>
</div>



We can drop features which show ``NaN`` correlation.


```python
df = df.drop(columns=['surcharge'])
```


```python
corr = df.corr(method ='spearman')
```

### Heatmap
Completing the data science workflow from sourcing big data, wrangling it using Amazon Athena to well formed schema, bringing adequate sample data from Athena to notebook environment, conducting exploratory data analysis, and finally visualizing the results.


```python
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
```


```python
heatmap(corr)
```


![Seaborn Correlation Plot](https://s3.amazonaws.com/cloudstory/notebooks-media/seaborn-corr.png)

