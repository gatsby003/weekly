# weekly

Weekly uses the Spotify API to pull your playing history and generates a weekly wrapped sent directly to your email. The system is implemented using Python, Airflow and Docker.

1. Flask App : For authorizing weekly to access your spotify history
2. Airflow : Run daily ETL jobs to load data to postgres and a weekly job to generate wrapped
