import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def growth_scatter(df):
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Confirmed"],
                        mode='lines+markers',
                        name='Confirmed Cases'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Recovered"],
                        mode='lines+markers',
                        name='Recovered Cases'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Deaths"],
                        mode='lines+markers',
                        name='Death Cases'))
    fig.update_layout(title="Growth of different types of cases",
                    xaxis_title="Date",yaxis_title="Number of Cases",legend=dict(x=0,y=1,traceorder="normal"))

    st.write(fig)

def weekly_increase(df):
    week_num=[]
    weekwise_confirmed=[]
    weekwise_recovered=[]
    weekwise_deaths=[]
    w=1
    for i in list(df["WeekOfYear"].unique()):
        weekwise_confirmed.append(df[df["WeekOfYear"]==i]["Confirmed"].iloc[-1])
        weekwise_recovered.append(df[df["WeekOfYear"]==i]["Recovered"].iloc[-1])
        weekwise_deaths.append(df[df["WeekOfYear"]==i]["Deaths"].iloc[-1])
        week_num.append(w)
        w=w+1

    fig = plt.figure(figsize=(8,5))
    plt.plot(week_num,weekwise_confirmed,linewidth=3)
    plt.plot(week_num,weekwise_recovered,linewidth=3)
    plt.plot(week_num,weekwise_deaths,linewidth=3)
    plt.ylabel("Number of Cases")
    plt.xlabel("Week Number")
    plt.title("Weekly progress of Different Types of Cases")
    # plt.xlabel
    st.pyplot(fig)

    fig, (ax1,ax2) = plt.subplots(1, 2,figsize=(15,5))
    sns.barplot(x=week_num,y=pd.Series(weekwise_confirmed).diff().fillna(0),ax=ax1)
    sns.barplot(x=week_num,y=pd.Series(weekwise_deaths).diff().fillna(0),ax=ax2)
    ax1.set_xlabel("Week Number")
    ax2.set_xlabel("Week Number")
    ax1.set_ylabel("Number of Confirmed Cases")
    ax2.set_ylabel("Number of Death Cases")
    ax1.set_title("Weekly increase in Number of Confirmed Cases")
    ax2.set_title("Weekly increase in Number of Death Cases")

    st.pyplot(fig)

def mortality(df):
    df["Mortality Rate"]=(df["Deaths"]/df["Confirmed"])*100
    df["Recovery Rate"]=(df["Recovered"]/df["Confirmed"])*100
    df["Active Cases"]=df["Confirmed"]-df["Recovered"]-df["Deaths"]
    df["Closed Cases"]=df["Recovered"]+df["Deaths"]

    st.write("Average Mortality Rate = ",f'{df["Mortality Rate"].mean():.2f}')
    st.write("Median Mortality Rate = ",f'{df["Mortality Rate"].median():.2f}')
    st.write("Average Recovery Rate = ",f'{df["Recovery Rate"].mean():.2f}')
    st.write("Median Recovery Rate = ",f'{df["Recovery Rate"].median():.2f}')

    #Plotting Mortality and Recovery Rate 
    fig = make_subplots(rows=2, cols=1,
                    subplot_titles=("Recovery Rate", "Mortatlity Rate"))
    fig.add_trace(
        go.Scatter(x=df.index, y=(df["Recovered"]/df["Confirmed"])*100,name="Recovery Rate"),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=(df["Deaths"]/df["Confirmed"])*100,name="Mortality Rate"),
        row=2, col=1
    )
    fig.update_layout(height=1000,legend=dict(x=0,y=0.5,traceorder="normal"))
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Recovery Rate", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_yaxes(title_text="Mortality Rate", row=1, col=2)

    st.write(fig)

def growth_factor(df):
    daily_increase_confirm=[]
    daily_increase_recovered=[]
    daily_increase_deaths=[]
    for i in range(df.shape[0]-1):
        daily_increase_confirm.append(((df["Confirmed"].iloc[i+1]/df["Confirmed"].iloc[i])))
        daily_increase_recovered.append(((df["Recovered"].iloc[i+1]/df["Recovered"].iloc[i])))
        daily_increase_deaths.append(((df["Deaths"].iloc[i+1]/df["Deaths"].iloc[i])))
    daily_increase_confirm.insert(0,1)
    daily_increase_recovered.insert(0,1)
    daily_increase_deaths.insert(0,1)

    fig = plt.figure(figsize=(15,7))
    plt.plot(df.index,daily_increase_confirm,label="Growth Factor Confiremd Cases",linewidth=3)
    plt.plot(df.index,daily_increase_recovered,label="Growth Factor Recovered Cases",linewidth=3)
    plt.plot(df.index,daily_increase_deaths,label="Growth Factor Death Cases",linewidth=3)
    plt.xlabel("Timestamp")
    plt.ylabel("Growth Factor")
    plt.title("Growth Factor of different Types of Cases")
    plt.axhline(1,linestyle='--',color='black',label="Baseline")
    plt.xticks(rotation=90)
    plt.legend()

    st.pyplot(fig)

def daily_increase(df):
    st.write("Average increase in number of Confirmed Cases every day: ",np.round(df["Confirmed"].diff().fillna(0).mean()))
    st.write("Average increase in number of Recovered Cases every day: ",np.round(df["Recovered"].diff().fillna(0).mean()))
    st.write("Average increase in number of Deaths Cases every day: ",np.round(df["Deaths"].diff().fillna(0).mean()))

    fig=go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Confirmed"].diff().fillna(0),mode='lines+markers',
                        name='Confirmed Cases'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Recovered"].diff().fillna(0),mode='lines+markers',
                        name='Recovered Cases'))
    fig.add_trace(go.Scatter(x=df.index, y=df["Deaths"].diff().fillna(0),mode='lines+markers',
                        name='Death Cases'))
    fig.update_layout(title="Daily increase in different types of Cases",
                    xaxis_title="Date",yaxis_title="Number of Cases",legend=dict(x=0,y=1,traceorder="normal"))
    st.write(fig)

def double_days(df):
    c=1000
    double_days=[]
    C=[]
    while(1):
        double_days.append(df[df["Confirmed"]<=c].iloc[[-1]]["Days Since"][0])
        C.append(c)
        c=c*2
        if(c<df["Confirmed"].max()):
            continue
        else:
            break

    doubling_rate=pd.DataFrame(list(zip(C,double_days)),columns=["Cases","Days since first Case"])
    doubling_rate["Doubling Days"]=doubling_rate["Days since first Case"].diff().fillna(doubling_rate["Days since first Case"])

    st.write(doubling_rate)
