import {
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib"
import React, { ReactNode } from "react"
import maplibregl from "maplibre-gl"
import { Signer } from "@aws-amplify/core"
import { config, CognitoIdentityCredentials } from "aws-sdk"


class LocationMap extends StreamlitComponentBase {
  public render = (): ReactNode => {
    const mapName = this.props.args["name"]
    const lat = this.props.args["lat"]
    const lon = this.props.args["lon"]
    const zoom = this.props.args["zoom"]
    const pitch = this.props.args["pitch"]
    const identityPoolId = this.props.args["identity"]
    
    // extract the region from the Identity Pool ID
    config.region = identityPoolId.split(":")[0]
    
    // instantiate a Cognito-backed credential provider
    const credentials = new CognitoIdentityCredentials({
      IdentityPoolId: identityPoolId,
    })
       
    /**
     * Sign requests made by MapLibre GL JS using AWS SigV4.
     */
    function transformRequest(url="", resourceType="") {
      if (resourceType === "Style" && !url.includes("://")) {
        // resolve to an AWS URL
        url = `https://maps.geo.${config.region}.amazonaws.com/maps/v0/maps/${url}/style-descriptor`;
      }

      if (url.includes("amazonaws.com")) {
        // only sign AWS requests (with the signature as part of the query string)
        return {
          url: Signer.signUrl(url, {
            access_key: credentials.accessKeyId,
            secret_key: credentials.secretAccessKey,
            session_token: credentials.sessionToken,
          }),
        }
      }

      // don't sign
      return { url }
    }

    /**
     * Initialize a map.
     */
    async function initializeMap() {
      // load credentials and set them up to refresh
      await credentials.getPromise()

      // Initialize the map
      const map = new maplibregl.Map({
        container: "map",
        center: [lon, lat], // initial map centerpoint
        zoom: zoom, // initial map zoom
        style: mapName,
        pitch: pitch,
        transformRequest,
      })
      const options = {
        showCompass: true,
        showZoom: true,
        visualizePitch: true ? pitch : false
      }
      map.addControl(new maplibregl.NavigationControl(options), "top-left")
    }    

    initializeMap()

    return (
      <div id="map" />
    )
  }
}

export default withStreamlitConnection(LocationMap)
