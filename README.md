# status
ooi-ui-status
===============

Ocean Observatories Initiative - User Interface Status Service.

Brief WSGI service supporting request for all routes in OOI UI Flask App; then process each static route for execution status.


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

Verify OOI UI services are operational by using a web browser and navigating to:

    http://localhost:4000/list_routes

### Running the services instance
    python status_handler.py

### Service Tests
Test your initial setup by running from status directory:

    python status_handler.py

Verify service is operational by using a web browser and navigating to:

    http://localhost:4070/service=alive

Verify postgres database connections are configured properly by using a web browser and navigating to:

    http://localhost:4070/service=checkconnections

Exercise performance status(es) by using a web browser and navigating to:

    http://localhost:4070/service=fetchstats

Verify data has been committed to postgresql database, in table performance_stats, using psql:

    $ psql pstats
    pstats=# select id, timestamp, status_code, timespan, route_url, route_endpoint from performance_stats;

### Trouble Shooting

If the OOI UI services are not running, and you try to exercise the performance status(es) by navigating to:

    http://localhost:4070/service=fetchstats

The following error message will be displayed:

    {"ERROR": "failed to retrieve routes; verify OOI UI services are runnning and value of config setting 'routes_command'"}

Corrective action includes:

    Verify the OOI UI services are running.
    If the OOI UI services are not running, start them.
    If the OOI UI services are running:
        verify the status_settings.yml contains the correct values for the routes_url, routes_command,
        routes_port settings. (example routes_command: /list_routes)

----

