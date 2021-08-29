import streamlit as st
import location_api as loc
from location_map_component.location_map import location_map

# Cognito pool ID
# Learn how to create your own ID here
# https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools.html
_IDENTITY = "replace-with-your-cognito-identity-pool-id"

st.header('Amazon Location Experiment')

tabs = st.radio('Choose Amazon Location Feature', 
    ('View ESRI Map', 'View HERE Map', 'List Resources'))

if tabs == 'View ESRI Map':
    location_map("explore.map", identity=_IDENTITY)

if tabs == 'View HERE Map':
    landmark = st.sidebar.selectbox(
        "View Landmark",
        ("Bhurj Khalifa", "Empire State Building", "Sydney Opera House", "London Eye", "World Trade Center")
    )
    if landmark == "London Eye":
        location_map("2-5D-Map", lon=-0.1196, lat=51.5033, zoom=15, pitch=50, identity=_IDENTITY)
    elif landmark == "Empire State Building":
        location_map("2-5D-Map", lon=-73.9857, lat=40.7484, zoom=15, pitch=30, identity=_IDENTITY)
    elif landmark == "Sydney Opera House":
        location_map("2-5D-Map", lon=151.2153, lat=-33.8568, zoom=15, pitch=40, identity=_IDENTITY)
    elif landmark == "World Trade Center":
        location_map("2-5D-Map", lon=-74.013382, lat=40.712742, zoom=14, pitch=40, identity=_IDENTITY)
    else:
        location_map("2-5D-Map", lon=55.2744, lat=25.1972, zoom=14, pitch=60, identity=_IDENTITY)

if tabs == 'List Resources':
    loc.list_resources()

