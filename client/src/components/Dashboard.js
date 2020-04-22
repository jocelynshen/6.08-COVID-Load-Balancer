import React from "react";
import { BrowserRouter, Route } from "react-router-dom";
import "../css/Map.css";
import { get, post, getCity, getCountry } from "../utilities";
import {withGoogleMap,GoogleMap,withScriptjs,Marker, Circle, InfoWindow} from "react-google-maps";
import Geocode from "react-geocode";
import Autocomplete from "react-google-autocomplete"
const { SearchBox } = require("react-google-maps/lib/components/places/SearchBox");
import { Link } from "react-router-dom";
import marker from "../public/map-marker.png";
import HeatmapLayer from "react-google-maps/lib/components/visualization/HeatmapLayer";
import gpsButton from "../public/crosshairs-gps.png"
const _ = require("lodash");
const { compose, withProps, lifecycle } = require("recompose");
require("dotenv").config();
Geocode.setApiKey(process.env.REACT_APP_GOOGLE_API);
Geocode.enableDebug();

class Dashboard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      center: { lat: 39.0911, lng: -94.4155 },
      zoom: 6,
      data: []
    }
    this.mapRef = React.createRef((ref) => {this.mapRef = ref;});
  }

  shouldComponentUpdate(nextProps, nextState) {
    console.log("next props", nextProps);
    console.log("next state", nextState);
      if (this.state.center.lat !== nextState.center.lat || this.state.center.lng !== nextState.center.lng || this.state.data != nextState.data) {
        return true
      } else {
        return false
      }
    }

  componentDidMount() {
    document.title = "Dashboard";
    //this.handleGeolocationNoSSL();
    fetch('http://608dev-2.net/sandbox/sc/team106/database.py?user=admin&password=adminpassword')
        .then(response => response.json())
        .then(data => {
          this.setState({data: data.map((x) => {return {  location: new window.google.maps.LatLng(x["lat"],x["lon"]), weight: x["weight"]  }})})
        });
  }

  handleLocationNoPermission = () => {
    let lat = this.state.mapPosition.lat;
    let lng = this.state.mapPosition.lng;
    Geocode.fromLatLng(lat, lng).then(
      response => {
        const address = response.results[0].formatted_address,geoAddressArray = response.results[0].address_components;
        this.setState({
          address: address ? address : "",
          mapPosition: {lat: lat,lng: lng},
          addressArray: geoAddressArray,
          askForLocation: false,
        });
        if (this.state.userLocationAddressArray.length === 0){
          this.setState({userLocationAddressArray: geoAddressArray})
        }

      },
      error => {
        console.error(error);
      }
    );
  }

  handleGeolocationNoSSL = () => {
    get("http://ip-api.com/json", {}).then((data) => {
      if(data.status === "success") {
        if(data) {
          let lat = data.lat; let lng = data.lon
          Geocode.fromLatLng(lat, lng).then(
            response => {
              const address = response.results[0].formatted_address,
                geoAddressArray = response.results[0].address_components;
              this.setState({
                address: address ? address : "",
                mapPosition: {
                  lat: lat,
                  lng: lng
                },
                addressArray: geoAddressArray,
                askForLocation: false,
              });
              this.setState({userLocationAddressArray: geoAddressArray});
            },
            error => {
              console.error(error);
            }
          );
        } else {
          let coords = { lat: 42.3601, lng: -71.0589 };
          this.setState({mapPosition: coords, askForLocation: false });
        }
      }
      else {
        let coords = { lat: 42.3601, lng: -71.0589 };
        this.setState({mapPosition: coords, askForLocation: false });
      }
    });
  }

  onPlaceSelected = place => {
    console.log("PLACE", place);
    const latValue = place.geometry.location.lat(),
      lngValue = place.geometry.location.lng();
      this.nextLat = latValue;
      this.nextLng = lngValue;
    this.setState({ formattedPlaceAddress: place.formatted_address});
    this.state.mapRef.panTo(
        new window.google.maps.LatLng(latValue, lngValue)
      );
  };

  mapOnClick = pos => {
    let newLat = pos.latLng.lat(),newLng = pos.latLng.lng();
    this.nextLat = newLat;
    this.nextLng = newLng;
    // this.setState({center: {lat: newLat, lng: newLng}});
    this.state.mapRef.panTo(
      new window.google.maps.LatLng(newLat, newLng)
    )
  };

  onIdle = () => {
    if (this.nextLat != undefined && this.nextLng != undefined) {
      this.setState({zoom: this.state.mapRef.getZoom(), center: {lat: this.nextLat, lng: this.nextLng}});
      this.nextLat = undefined;
      this.nextLng = undefined;
    }
  }

  render() {
    const AsyncMap = compose(
  lifecycle({
    componentWillMount() {
      const refs = {}

      this.setState({
        bounds: null,
        markers: [],
        onMapMounted: ref => {
          this.setState({mapRef: ref});
          console.log("hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", this.state);
          refs.map = ref;
        },
        onBoundsChanged: () => {
          this.setState({
            bounds: refs.map.getBounds(),
            center: refs.map.getCenter(),
          })
        },
        onSearchBoxMounted: ref => {
          refs.searchBox = ref;
        },
        onPlacesChanged: () => {
          const places = refs.searchBox.getPlaces();
          const bounds = new google.maps.LatLngBounds();

          places.forEach(place => {
            if (place.geometry.viewport) {
              bounds.union(place.geometry.viewport)
            } else {
              bounds.extend(place.geometry.location)
            }
          });
          const nextMarkers = places.map(place => ({
            position: place.geometry.location,
          }));
          const nextCenter = _.get(nextMarkers, '0.position', this.state.center);

          this.setState({
            center: nextCenter,
            markers: nextMarkers,
          });
          // refs.map.fitBounds(bounds);
        },
      })
    },
  }),
  withScriptjs,
  withGoogleMap
)(props =>
  <GoogleMap
    ref={props.onMapMounted}
    // ref = {(ref) => this.mapRef = ref;}
    defaultZoom={15}
    center={this.state.center}
    onBoundsChanged={props.onBoundsChanged}
    google={window.google}
        bootstrapURLKeys={{
        libraries: 'visualization',
      }}
    onClick={this.mapOnClick}
    styles = {[{
        featureType: 'poi.business',
        elementType: 'labels',
        stylers: [{
            visibility: 'on'
        }]
    }]}
    zoom={this.state.zoom}
    onIdle = {this.onIdle}
  >

  <HeatmapLayer
    data={this.getData()}
    options={{radius: 20}}
  />

  <Marker
          google={window.google} position={this.state.center} icon={marker}/>

  <Autocomplete
      style={{
        width: "35%",
        height: "45px",
        position: `absolute`,
        top: "70px",
        borderRadius: "10px",
        border: "none",
        marginLeft: "1em",
        paddingLeft: "1em",
        boxShadow:
          "0 2px 10px 0 rgba(0, 0, 0, 0.1), 0 2px 10px 0 rgba(0, 0, 0, 0.19)",
        fontSize: "15px",
        fontFamily: "Josefin Sans"
      }}
      onPlaceSelected={(place) => {props.onPlaceSelected(place)}}
      types={["geocode"]}
      placeholder={this.state.formattedPlaceAddress ? this.state.formattedPlaceAddress : "Enter a location"}
    />

    <SearchBox
      ref={props.onSearchBoxMounted}
      bounds={props.bounds}
      controlPosition={google.maps.ControlPosition.TOP_LEFT}
      onPlacesChanged={props.onPlacesChanged}
    >
      <input
        type="text"
        placeholder="Customized your placeholder"
        style={{
          boxSizing: `border-box`,
          border: `1px solid transparent`,
          width: `240px`,
          height: `32px`,
          marginTop: `27px`,
          padding: `0 12px`,
          borderRadius: `3px`,
          boxShadow: `0 2px 6px rgba(0, 0, 0, 0.3)`,
          fontSize: `14px`,
          outline: `none`,
          textOverflow: `ellipses`,
        }}
      />
    </SearchBox>
    {props.markers.map((marker, index) =>
      <Marker key={index} position={marker.position} />
    )}
  </GoogleMap>
);

    return (
      <>
        <AsyncMap
          googleMapURL={"https://maps.googleapis.com/maps/api/js?key=" + process.env.REACT_APP_GOOGLE_API + "&libraries=places,visualization"}
          loadingElement={<div style={{ height: `100%` }} />}
          containerElement={<div style={{ height: "100vh", width: `100%`, position: `relative` }}/>}
          mapElement={<div style={{ height: `100%`, width: `100%`, position: `relative` }}/>}
        />

        <div id="right_over_map">
          <div className="column-right-align">
            <div className="trending-box">
              <div className="trending-text">
                <h3 className="trending-title">Dashboard</h3>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }
  getData = () => {
    return this.state.data;
    // return [new window.google.maps.LatLng(39.0911,-94.4155)]
  }
}

export default Dashboard;
