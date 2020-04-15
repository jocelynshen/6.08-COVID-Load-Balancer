import React from "react";
import { BrowserRouter, Route } from "react-router-dom";

import "../css/Map.css";
import { get, post, getCity, getCountry } from "../utilities";

import {withGoogleMap,GoogleMap,withScriptjs,Marker, Circle, InfoWindow} from "react-google-maps";
import Geocode from "react-geocode";
import Autocomplete from "react-google-autocomplete"
import { Link } from "react-router-dom";
import marker from "../public/map-marker.png";
import ReactLoading from "react-loading";

import gpsButton from "../public/crosshairs-gps.png"

require("dotenv").config();

Geocode.setApiKey(process.env.REACT_APP_GOOGLE_API);
Geocode.enableDebug();

class Dashboard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      center: { lat: 39.0911, lng: -94.4155 }
    }
    this.mapRef = React.createRef((ref) => {this.mapRef = ref;});
  }

  shouldComponentUpdate(nextProps, nextState) {
      if (this.state.center.lat !== nextState.center.lat || this.state.center.lng !== nextState.center.lng) {
        return true
      } else {
        return false
      }
    }

  componentDidMount() {
    document.title = "Dashboard";
    this.handleGeolocationNoSSL();
    //this.handleLocationNoPermission();
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
    const latValue = place.geometry.location.lat(),
      lngValue = place.geometry.location.lng();
      this.nextLat = latValue;
      this.nextLng = lngValue;
      this.setState({ formattedPlaceAddress: place.formatted_address, center: {lat: latValue, lng: lngValue}})
    this.mapRef.panTo(
        new window.google.maps.LatLng(latValue, lngValue)
      );
  };

  mapOnClick = pos => {
    let newLat = pos.latLng.lat(),newLng = pos.latLng.lng();
    this.nextLat = newLat;
    this.nextLng = newLng;
    this.setState({center: {lat: newLat, lng: newLng}});
    this.mapRef.panTo(
      new window.google.maps.LatLng(newLat, newLng)
    )
  };

  onIdle = () => {
    if (this.nextLat && this.nextLng) {
      this.setState({zoom: this.mapRef.getZoom(), mapPostion: {lat: this.nextLat, lng: this.nextLng}})
      Geocode.fromLatLng(this.nextLat, this.nextLng).then(
        response => {
          const address = response.results[0].formatted_address,
            geoAddressArray = response.results[0].address_components;
          if(getCountry(geoAddressArray).length > 0) {
            this.setState({
              address: address ? address : "",
              mapPosition: {
                lat: this.nextLat,
                lng: this.nextLng
              },
              addressArray: geoAddressArray,
            });
            this.nextLat = undefined;
            this.nextLng = undefined;
          }
        },
        error => {
          console.error(error);
        }
      );
    }
  }

  render() {
    const AsyncMap =
      withScriptjs(
      withGoogleMap
    (props => (
        <GoogleMap
          google={window.google}
          onClick={this.mapOnClick}
          zoom={6}
          center={this.state.center}
          // defaultOptions={{
          //   disableDefaultUI: true, // disable default map UI
          //   zoomControl: true,
          //   zoomControlOptions: {
          //     position: google.maps.ControlPosition.LEFT_BOTTOM
          //   },
          //   scaleControl: true,
          //   fullscreenControl: false,
          //   fullscreenControlOptions: {
          //     position: google.maps.ControlPosition.LEFT_BOTTOM
          //   },
          //   minZoom: 2,
          //   maxZoom: 12,
          // }}
          ref={(ref) => {
            this.mapRef = ref;
          }}
          onIdle = {this.onIdle}
        >
          <Marker
            google={window.google} position={this.state.center} icon={marker}/>
          <Circle
                defaultCenter={this.state.center}
                radius={this.state.value*1000}
                options= {{
                  strokeColor: "#fff",
                  fillColor: "#B1E0FD",
                  strokeWeight: "1"
                }}
              />

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
            onPlaceSelected={(place) => {this.onPlaceSelected(place)}}
            types={["(regions)"]}
            placeholder={this.state.formattedPlaceAddress ? this.state.formattedPlaceAddress : "Enter a location"}
          />
        </GoogleMap>
      ))
    );

    return (
      <>
        <AsyncMap
          googleMapURL={"https://maps.googleapis.com/maps/api/js?key=" + process.env.REACT_APP_GOOGLE_API + "&libraries=places"}
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
}

export default Dashboard;
