import streamlit as st
import pandas as pd
import boto3

client = boto3.client('location')

def list_resources():
    st.subheader('Maps')
    response = client.list_maps()
    st.write(pd.DataFrame.from_dict(response['Entries']))

    st.subheader('Place Indexes')
    response = client.list_place_indexes()
    st.write(pd.DataFrame.from_dict(response['Entries']))

    st.subheader('Trackers')
    response = client.list_trackers()
    st.write(pd.DataFrame.from_dict(response['Entries']))

    tracker = st.text_input('List Device Positions by Tracker', '')
    if tracker:
        st.subheader('Device positions by ' + tracker)
        response = client.list_device_positions(TrackerName=tracker)
        st.write(pd.DataFrame.from_dict(response['Entries']))

        st.subheader('Geofence consumers by ' + tracker)
        response = client.list_tracker_consumers(TrackerName=tracker)
        st.write(pd.DataFrame(response['ConsumerArns']))

    st.subheader('Route Calculators')
    response = client.list_route_calculators()
    st.write(pd.DataFrame.from_dict(response['Entries']))

    st.subheader('Geofence Collections')
    response = client.list_geofence_collections()
    st.write(pd.DataFrame.from_dict(response['Entries']))

    collection = st.text_input('List Geofences in collection', '')
    if collection:
        st.subheader('Geofences in ' + collection)
        response = client.list_geofences(CollectionName=collection)
        st.write(pd.DataFrame.from_dict(response['Entries']))
