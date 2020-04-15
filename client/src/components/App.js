import React from "react";
import Route from "react-router-dom/es/Route";
import Switch from "react-router-dom/es/Switch";
import { Router, Link, Location } from '@reach/router';

import posed, { PoseGroup } from 'react-pose';

import Root from "./Root";
import Dashboard from "./Dashboard";

import "../utilities.css";


const RouteContainer = posed.div({
  enter: { opacity: 1, delay: 300, beforeChildren: 300 },
  exit: { opacity: 0 }
});


const App = () => (

  <Route
    render={({ location }) => (
      <div>
          <PoseGroup>
            <RouteContainer key={location.pathname}>
              <Switch location={location}>
                <Route exact path="/" component={Root} key="home" />
                <Route path="/dashboard" component={Dashboard} key="dashboard" />
              </Switch>
            </RouteContainer>
          </PoseGroup>
      </div>
    )}
  />
);

export default App;
