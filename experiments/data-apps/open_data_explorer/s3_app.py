import streamlit as st
from api.streamlit_experiments import s3

st.header('Amazon S3 App')
tabs = st.radio('Choose S3 action', 
    ('List Bucket Contents', 'Query CSV', 'Search Own Buckets', 'Create Own Bucket'))

if tabs == 'Search Buckets':
    s3.search_buckets()
elif tabs == 'List Bucket Contents':
    s3.list_bucket_contents()
elif tabs == 'Query CSV':
    s3.s3_select()
else:
    s3.create_bucket()

