## Cloud Experiments

**Sample notebooks, starter apps, and low/no code guides for rapidly (within 60-minutes) building and running open innovation experiments on AWS Cloud**

Cloud experiments follow step-by-step workflow for performing analytics, machine learning, AI, and data science on AWS cloud. We present guidance on using AWS Cloud programmatically or visually using the console, introduce relevant AWS services, explaining the code, reviewing the code outputs, evaluating alternative steps in our workflow, and ultimately designing an abstrated reusable API for rapidly deploying these experiments on AWS cloud.

You may want to run these notebooks using [Amazon SageMaker](https://aws.amazon.com/sagemaker/). Amazon SageMaker is a fully-managed service that covers the entire machine learning workflow to label and prepare your data, choose an algorithm, train the model, tune and optimize it for deployment, make predictions, and take action.

### [COVID Insights](https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/covid)
This notebook provides a catalog of open datasets for deriving insights related to COVID-19 and helping open source and open data community to collaborate in fighting this global threat. The notebook provides (a) reusable API to speed up open data analytics related to COVID-19, customized for India however can be adopted for other countries, (b) sample usage of the API, (c) documentation of insights, and (d) catalog of open datasets referenced.


### [Comprehend Medical for Electronic Health Records](https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/comprehend-medical-ehr)
Amazon Comprehend Medical is an API-level service which is HIPAA eligible and uses machine learning to extract medical information with high accuracy. The service eliminates the barriers to entry to access the biomedical knowledge stored in natural language text - from the research literature that entails biological processes and therapeutic mechanisms of action to the Electronic Medical Records that have the patients’ journeys through our healthcare systems documented. The service also helps us comb through that information and study relationships like symptoms, diagnosis, medication, dosage while redacting the Protected Health Information (PHI). This is an illustrative notebook that includes a step-by-step workflow for analyzing health data on the cloud.


### [Video Analytics](https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/video-analytics/)
Analyzing video based content requires transforming from one media format (video or audio) to another format (text or numeric) while identifying relevant structure in the resulting format. This multi-media transformation requires machine learning based recognition. Analytics libraries can work on the transformed data to determine the required outcomes including visualizations and charts. The structured data in text or numeric format can also be reused as input to training new machine learning models.

### [Using AI Services for Analyzing Public Data](https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/ai-services/)

So far we have been working with structured data in flat files as our data source. What if the source is images and unstructured text. AWS AI services provide vision, transcription, translation, personalization, and forecasting capabilities without the need for training and deploying machine learning models. AWS manages the machine learning complexity, you just focus on the problem at hand and send required inputs for analysis and receive output from these services within your applications.

### [Exploring data with Python and Amazon S3 Select](https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/exploring-data/)

For this notebook let us start with a big open dataset. Big enough that we will struggle to open it in Excel on a laptop. Excel has around million rows limit. We will setup AWS services to source from a 270GB data source, filter and store more than 8 million rows or 100 million data points into a flat file, extract schema from this file, transform this data, load into analytics tools, run Structured Query Language (SQL) on this data.

### [Optimizing data for analysis with Amazon Athena and AWS Glue](https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/optimizing-data/)

We will continue our open data analytics workflow starting with the AWS Console then moving to using the notebook. Using AWS Glue we can automate creating a metadata catalog based on flat files stored on Amazon S3. Glue is a fully managed extract, transform, and load (ETL) service that makes it easy for customers to prepare and load their data for analytics. You can create and run an ETL job with a few clicks in the AWS Management Console. You simply point AWS Glue to your data stored on AWS, and AWS Glue discovers your data and stores the associated metadata (e.g. table definition and schema) in the AWS Glue Data Catalog. Once cataloged, your data is immediately searchable, queryable, and available for ETL.

### [Cloudstory API](https://github.com/aws-samples/aws-open-data-analytics-notebooks/tree/master/cloudstory-api/)

Cloudstory API Python module and demo of using the API. The cloudstory API is documented in the other notebooks listed here.

## License

This library is licensed under the Apache 2.0 License. 
