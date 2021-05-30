import streamlit as st
import pandas as pd
from api.streamlit_experiments import eda

st.header('Exploratory Data Analysis App')

st.subheader('Dataset')
df = pd.read_csv('census-income.csv')
st.write(df.head(20))

st.write(f'Rows, Columns: {df.shape}')

st.subheader('Correlation')
eda.correlate(df)

