# Amazon Location Experiment

This experiment demonstrates Amazon Location Service, creates a Streamlit component for displaying maps created within the service, creates high level API for rapidly experimenting with the service features.

First create your own [Cognito Identity Pool ID](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools.html) and replace as value for `_IDENTITY` variable in the `location_app.py` file. Also create a HERE map with the name `2-5D-Map` and a default `explore.map` ESRI map created by the Amazon Location Console Explore tool.

Start the demo by running `streamlit run location_app.py` command in terminal.

![Location Experiment App](location-experiment.png)  

