import React from "react";
import { BrowserRouter, Route } from "react-router-dom";
import { Element } from "react-scroll";
import { Link as ScrollLink, animateScroll as scroll } from "react-scroll";
import GoogleLogin, { GoogleLogout } from "react-google-login";
import "../css/Root.css";
import { get, post } from "../utilities";

import Dashboard from "./Dashboard.js";
import ReactLoading from "react-loading";

class Root extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      userId: null,
      isLoading: false,
      getStarted: true
    };
  }

  componentDidMount() {
    document.title = "covid";
    this.setState({isLoading: true})
  }

  render() {
    return (
      <Dashboard/>
    );
  }
}

export default Root;
