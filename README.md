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

----

