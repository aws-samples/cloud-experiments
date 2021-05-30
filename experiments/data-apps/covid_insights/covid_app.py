import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from api.streamlit_experiments import covid as cov

st.title('COVID Exploratory Data Analysis')

# Data from https://www.kaggle.com/sudalairajkumar/novel-corona-virus-2019-dataset?select=covid_19_data.csv

covid = pd.read_csv('494724_1196190_compressed_covid_19_data.csv.zip')

# Dropping column as SNo is of no use, and 'Province/State' contains too many missing values
covid.drop(['SNo'], 1, inplace=True)

st.header('Dataset')
st.write(covid)

# Converting 'Observation Date' into Datetime format
covid['ObservationDate']=pd.to_datetime(covid['ObservationDate'])

# Grouping different types of cases as per the date
datewise = covid.groupby(['ObservationDate']).agg({
    'Confirmed': 'sum',
    'Recovered': 'sum',
    'Deaths': 'sum'
    })

datewise['Days Since'] = datewise.index-datewise.index.min()
datewise["WeekOfYear"]=datewise.index.weekofyear

india_data=covid[covid["Country/Region"]=="India"]
datewise_india=india_data.groupby(["ObservationDate"]).agg({"Confirmed":'sum',"Recovered":'sum',"Deaths":'sum'})
datewise_india['Days Since'] = datewise_india.index-datewise.index.min()
datewise_india["WeekOfYear"]=datewise_india.index.weekofyear

st.header('Global Analysis')

st.line_chart(datewise[['Confirmed', 'Deaths', 'Recovered']])

st.subheader('Global Growth Factor')
cov.growth_factor(datewise)

st.subheader('India Growth Factor')
cov.growth_factor(datewise_india)

st.subheader('Global Weekly Growth of Cases')
cov.weekly_increase(datewise)

st.subheader('India Weekly Growth of Cases')
cov.weekly_increase(datewise_india)

st.subheader('Global Doubling Rate')
cov.double_days(datewise)

st.subheader('India Doubling Rate')
cov.double_days(datewise_india)

st.subheader('Daily Growth')
cov.growth_scatter(datewise)

st.subheader('Recovery and Mortality')
cov.mortality(datewise)

st.subheader('Daily Increases Stats')
cov.daily_increase(datewise)

st.header('Countrywise Analysis')

#Calculating countrywise Mortality and Recovery Rate
countrywise=covid[covid["ObservationDate"]==covid["ObservationDate"].max()].groupby(["Country/Region"]).agg({"Confirmed":'sum',"Recovered":'sum',"Deaths":'sum'}).sort_values(["Confirmed"],ascending=False)
countrywise["Mortality"]=(countrywise["Deaths"]/countrywise["Confirmed"])*100
countrywise["Recovery"]=(countrywise["Recovered"]/countrywise["Confirmed"])*100

fig, (ax1, ax2) = plt.subplots(2, 1,figsize=(10,12))
top_15_confirmed=countrywise.sort_values(["Confirmed"],ascending=False).head(15)
top_15_deaths=countrywise.sort_values(["Deaths"],ascending=False).head(15)
sns.barplot(x=top_15_confirmed["Confirmed"],y=top_15_confirmed.index,ax=ax1)
ax1.set_title("Top 15 countries as per Number of Confirmed Cases")
sns.barplot(x=top_15_deaths["Deaths"],y=top_15_deaths.index,ax=ax2)
ax2.set_title("Top 15 countries as per Number of Death Cases")

st.pyplot(fig)

st.header('India Analysis')

st.line_chart(datewise_india[['Confirmed', 'Deaths', 'Recovered']])

st.write(datewise_india.iloc[-1])
st.write("Total Active Cases: ",datewise_india["Confirmed"].iloc[-1]-datewise_india["Recovered"].iloc[-1]-datewise_india["Deaths"].iloc[-1])
st.write("Total Closed Cases: ",datewise_india["Recovered"].iloc[-1]+datewise_india["Deaths"].iloc[-1])

st.subheader('India Growth Daily')
cov.growth_scatter(datewise_india)

st.subheader('India Daily Increase in Cases')
cov.daily_increase(datewise_india)

st.subheader('India Recovery and Mortality')
cov.mortality(datewise_india)

st.subheader('India Compared with Other Countries')

Italy_data=covid[covid["Country/Region"]=="Italy"]
US_data=covid[covid["Country/Region"]=="US"]
spain_data=covid[covid["Country/Region"]=="Spain"]
datewise_Italy=Italy_data.groupby(["ObservationDate"]).agg({"Confirmed":'sum',"Recovered":'sum',"Deaths":'sum'})
datewise_US=US_data.groupby(["ObservationDate"]).agg({"Confirmed":'sum',"Recovered":'sum',"Deaths":'sum'})
datewise_Spain=spain_data.groupby(["ObservationDate"]).agg({"Confirmed":'sum',"Recovered":'sum',"Deaths":'sum'})

max_ind=datewise_india["Confirmed"].max()
fig = plt.figure(figsize=(12,6))
plt.plot(datewise_Italy[(datewise_Italy["Confirmed"]>0)&(datewise_Italy["Confirmed"]<=max_ind)]["Confirmed"],label="Confirmed Cases Italy",linewidth=3)
plt.plot(datewise_US[(datewise_US["Confirmed"]>0)&(datewise_US["Confirmed"]<=max_ind)]["Confirmed"],label="Confirmed Cases USA",linewidth=3)
plt.plot(datewise_Spain[(datewise_Spain["Confirmed"]>0)&(datewise_Spain["Confirmed"]<=max_ind)]["Confirmed"],label="Confirmed Cases Spain",linewidth=3)
plt.plot(datewise_india[datewise_india["Confirmed"]>0]["Confirmed"],label="Confirmed Cases India",linewidth=3)
plt.xlabel("Date")
plt.ylabel("Number of Confirmed Cases")
plt.title("Growth of Confirmed Cases")
plt.legend()
plt.xticks(rotation=90)

st.write("It took",datewise_Italy[(datewise_Italy["Confirmed"]>0)&(datewise_Italy["Confirmed"]<=max_ind)].shape[0],"days in Italy to reach number of Confirmed Cases equivalent to India")
st.write("It took",datewise_US[(datewise_US["Confirmed"]>0)&(datewise_US["Confirmed"]<=max_ind)].shape[0],"days in USA to reach number of Confirmed Cases equivalent to India")
st.write("It took",datewise_Spain[(datewise_Spain["Confirmed"]>0)&(datewise_Spain["Confirmed"]<=max_ind)].shape[0],"days in Spain to reach number of Confirmed Cases equivalent to India")
st.write("It took",datewise_india[datewise_india["Confirmed"]>0].shape[0],"days in India to reach",max_ind,"Confirmed Cases")

st.pyplot(fig)

