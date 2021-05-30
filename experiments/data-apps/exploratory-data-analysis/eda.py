import streamlit as st
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Correlate features within a dataframe
def correlate(df):
    corr = df.corr()
    sns.set(style="white")

    fig = plt.figure(figsize=(9,7))
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    sns.heatmap(corr, vmax=0.3, center=0, cmap=cmap,
        annot=True, linewidths=0.5, fmt="3.2f", square=True)

    st.pyplot(fig)