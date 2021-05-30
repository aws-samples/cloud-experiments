import urllib.request
import bs4
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
import os.path
from os import path

def linear_regression(df):
    fig, ax = plt.subplots(1, 3, figsize=(15,5))
    sns.regplot(x='Confirmed', y='Active', data=df, ax=ax[0])
    sns.regplot(x='Confirmed', y='Discharged', data=df, ax=ax[1])
    sns.regplot(x='Confirmed', y='Death', data=df, ax=ax[2])
    fig.show()    

def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: pink' if v else '' for v in is_max]

def summary_stats(df):
    summary = df.drop(columns=['State']).sum()
    df2 = summary.to_frame()
    df2 = df2.rename(columns={0: 'Latest'})
    return df2.style.apply(highlight_max,subset=['Latest'])

def display_stats(df):
    df = df.sort_values(by=['Active'], ascending=False)
    return df.style.apply(highlight_max,subset=['Confirmed', 'Active', 'Discharged', 
                                                'Death','Indian','Foreign'])

def get_today_stats(force = False):
    today_file = datetime.now().strftime('%Y-%m-%d') + '-covid-india-stats.csv'

    if path.exists(today_file) and not force:
        stats_df= pd.read_csv(today_file)
        print('Stats file exists: ' + today_file)
    else:
        print('Creating stats for today...')
        with urllib.request.urlopen('https://www.mohfw.gov.in/') as response:
            page = response.read()
            html = bs4.BeautifulSoup(page, 'lxml')

        df_cols = []
        # stats page has multiple tables
        tables = html.findAll("table", {"class": "table-dark"})
        for table in tables:
            # only stats table has rows (tr tag)
            if table.thead.tr.th.strong.string == 'S. No.':
                for th in table.thead.tr:
                    if th.string:
                        df_cols.append(th.string.strip())
                    else:
                        df_cols.append(th.strong.text.strip())

                while '' in df_cols:
                    df_cols.remove('')

                stats_df = pd.DataFrame(columns = df_cols)

                i = 0
                for tr in table.tbody:
                    df_row = []
                    df_data = []
                    for td in tr:
                        if len(df_row) == len(df_cols):
                            # print(df_row)
                            stats_df.loc[i] = df_row
                            i = i + 1
                            df_row = []
                        if type(td) is bs4.element.Tag:
                            df_row.append(td.string)

        stats_df = stats_df.drop(columns=['S. No.'])
        stats_df = stats_df.rename(columns={'Name of State / UT': 'State',
                    'Total Confirmed cases (Indian National)': 'Indian', 
                    'Total Confirmed cases ( Foreign National )': 'Foreign',
                    'Cured/Discharged/Migrated': 'Discharged'})
        stats_df['Indian'] = stats_df['Indian'].astype(int)
        stats_df['Foreign'] = stats_df['Foreign'].astype(int)
        stats_df['Discharged'] = stats_df['Discharged'].astype(int)
        stats_df['Death'] = stats_df['Death'].astype(int)
        stats_df['Confirmed'] = stats_df['Indian'] + stats_df['Foreign']
        stats_df['Active'] = stats_df['Indian'] + stats_df['Foreign'] - stats_df['Discharged'] - stats_df['Death']

        stats_df.to_csv(today_file, index=False)
        print('Stats file for today saved: ' + today_file)
    
    return stats_df