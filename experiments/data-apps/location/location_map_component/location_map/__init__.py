import os
import streamlit.components.v1 as components
import uuid

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
# (This is, of course, optional - there are innumerable ways to manage your
# release process.)
_RELEASE = True

# Declare a Streamlit component. `declare_component` returns a function
# that is used to create instances of the component. We're naming this
# function "_component_func", with an underscore prefix, because we don't want
# to expose it directly to users. Instead, we will create a custom wrapper
# function, below, that will serve as our component's public API.

# It's worth noting that this call to `declare_component` is the
# *only thing* you need to do to create the binding between Streamlit and
# your component frontend. Everything else we do in this file is simply a
# best practice.

if not _RELEASE:
    _component_func = components.declare_component(
        # We give the component a simple, descriptive name ("location_map"
        # does not fit this bill, so please choose something better for your
        # own component :)
        "location_map",
        # Pass `url` here to tell Streamlit that the component will be served
        # by the local dev server that you run via `npm run start`.
        # (This is useful while your component is in development.)
        url="http://localhost:3001",
    )
else:
    # When we're distributing a production version of the component, we'll
    # replace the `url` param with `path`, and point it to to the component's
    # build directory:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("location_map", path=build_dir)


# Create a wrapper function for the component. This is an optional
# best practice - we could simply expose the component function returned by
# `declare_component` and call it done. The wrapper allows us to customize
# our component's API: we can pre-process its input args, post-process its
# output value, and add a docstring for users.
def location_map(name, lon=-123.1187, lat=49.2819, zoom=10, pitch=0, identity='', key=None):
    component_value = _component_func(
        name=name, 
        lon=lon, 
        lat=lat,
        zoom=zoom, 
        pitch=pitch,
        identity=identity,
        key=str(uuid.uuid4()), 
        default=0)
    return component_value


# Add some test code to play with the component while it's in development.
# During development, we can run this just as we would any other Streamlit
# app: `$ streamlit run location_map/__init__.py`
if not _RELEASE:
    import streamlit as st
    _IDENTITY = "us-east-1:e74fc977-4241-4a56-8bdd-49ea4455f8cf"
    st.subheader("Does this display the map?")

    location_map("explore.map", identity=_IDENTITY)

    location_map(
        "2-5D-Map", 
        lon=-73.9857, lat=40.7484, 
        zoom=16, pitch=30, 
        identity=_IDENTITY)
