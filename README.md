# status
ooi-ui-status
===============

Ocean Observatories Initiative - User Interface Status Service.

Brief WSGI service supporting request for all routes in OOI UI Flask App; then process each static route for execution status


## Service endpoints
The WSGI service endpoints are listed and defined below:

    /service=alive
    /service=checkconnections
    /service=fetchstats


### Configuration
Be sure to edit your `status_settings.yml` file to the correct URLs and Database Connectors.

### Service setup
Ensure you have the following:

Postgresql database with performance_stats table, e.g:

CREATE TABLE performance_stats (
    id SERIAL PRIMARY KEY,
    timestamp text NOT NULL,
    status_code text NOT NULL,
    url_processed text NOT NULL,
    route_url text NOT NULL,
    route_endpoint text NOT NULL,
    timespan float NOT NULL
);

### Running the services instance
    python status_handler.py

### Service Tests
Test your initial setup by running from status directory:

    python status_handler.py

Verify you are exercising server by using a web browser and navigating to:

    http://localhost:4070/service=alive

Verify postgres database connections are configured properly by using a web browser and navigating to:

    http://localhost:4070/service=checkconnections

Exercise performance status(es) by using a web browser and navigating to:

    http://localhost:4070/service=fetchstats

Verify data has been committed to postgresql database, in table performance_stats, using psql:

$ psql pstats
pstats=# select id, timestamp, status_code, timespan, route_url, route_endpoint from performance_stats;

Results should resemble following sample output:

 id |      timestamp      | status_code | timespan |        route_url         |                route_endpoint
----+---------------------+-------------+----------+--------------------------+-----------------------------------------------
  1 | 2015-02-09 17:57:11 | 401         | 0.003398 | /user                    | main.get_current_user
  2 | 2015-02-09 18:00:36 | 200         | 0.135958 | /uframe/platformlocation | uframe.get_platform_deployment_geojson_single
  3 | 2015-02-09 18:00:36 | 204         | 0.003754 | /uframe/display_name     | uframe.get_display_name
  4 | 2015-02-09 18:00:36 | 200         | 0.014396 | /uframe/get_data         | uframe.get_data
  5 | 2015-02-09 18:00:36 | 401         | 0.003767 | /watch/user              | main.get_watch_user
  6 | 2015-02-09 18:00:36 | 401         | 0.003804 | /watch/open              | main.get_watch_opened
  7 | 2015-02-09 18:00:36 | 200         | 0.598258 | /instrument_deployments  | main.get_instrument_deployments
  8 | 2015-02-09 18:00:36 | 200         | 0.327326 | /platform_deployments    | main.get_platform_deployments
  9 | 2015-02-09 18:00:36 | 200         | 0.005571 | /operator_event_type     | main.get_operator_event_types
 10 | 2015-02-09 18:00:36 | 204         | 0.004658 | /operator_event          | main.get_operator_events
 11 | 2015-02-09 18:00:36 | 200         | 0.004912 | /organization            | main.get_organizations
 12 | 2015-02-09 18:00:36 | 200         | 0.003526 | /list_routes             | main.list_routes
 13 | 2015-02-09 18:00:36 | 401         | 0.003297 | /user_scopes             | main.get_user_scopes
 14 | 2015-02-09 18:00:36 | 500         | 0.015229 | /annotations             | main.get_annotations
 15 | 2015-02-09 18:00:36 | 200         | 0.005302 | /parameters              | main.get_parameters
 16 | 2015-02-09 18:00:36 | 401         |  0.00346 | /user_roles              | main.get_user_roles
 17 | 2015-02-09 18:00:36 | 500         | 0.007738 | /logged_in               | main.logged_in
 18 | 2015-02-09 18:00:36 | 200         | 0.005197 | /streams                 | main.get_streams
 19 | 2015-02-09 18:00:36 | 200         | 0.010243 | /arrays                  | main.get_arrays
 20 | 2015-02-09 18:00:36 | 401         | 0.004004 | /token                   | main.get_token
 21 | 2015-02-09 18:00:36 | 204         | 0.004617 | /watch                   | main.get_watches
 22 | 2015-02-09 18:00:36 | 401         | 0.003294 | /user                    | main.get_current_user
(22 rows)

pstats=#



----

