import time
import datetime
import pendulum
import os

import requests

from airflow.models import Variable
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator

from sqlalchemy import create_engine

import pandas as pd

@dag(
    dag_id="daily_spotify_dag",
    schedule_interval="0 0 * * *",
    start_date=pendulum.datetime(2022, 12, 14, tz="UTC"),
    catchup=True,
    dagrun_timeout=datetime.timedelta(minutes=60),
    params={
        "user_id": 1
    }
)
def process_listening_history():
    create_history_table = PostgresOperator(
        task_id="create_history_table",
        postgres_conn_id="spotify_etl",
        sql="sql/history.sql",
    )

    @task
    def load_songs():
        # refresh access token -> get songs -> load in db
        re = requests.post(
            url='https://accounts.spotify.com/api/token',
            data={
                "grant_type": "refresh_token",
                "refresh_token": Variable.get('REFRESH_TOKEN')
            },
            headers={
                "Authorization": Variable.get('BEARER_TOKEN'),
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        if re.status_code != 200:
            return 1

        access_token = re.json()['access_token']
        print("Token Refreshed")

        def get_songs(time_stamp):
            r = requests.get(
                    url = 'https://api.spotify.com/v1/me/player/recently-played',
                    params={
                        "before": time_stamp,
                        "limit": 50
                    },
                    headers={
                        "Authorization": "Bearer " + access_token,
                        "Content-Type": "application/json"
                    }
                )

            if r.status_code == 200 and len(r.json().get('items')) > 0:
                return r.json().get('items')
            return None
        
        def get_artist_name(d):
            artist_list = d.get('track').get('artists')
            ls = []
            for a in artist_list:
                ls.append(a.get('name'))
            return ' '.join(ls)

        def get_songs_for_all_day():
            time_stamp = int(time.time() * 1e3)
            jump = 7200 # 2 hr jump
            
            df_list = []
            # doing 12 , 2 hr jumps to hopefully collect songs throughout the day
            for i in range(12):
                print(f"Getting songs for {time_stamp} slot {i}")
                songs = get_songs(time_stamp)
                if songs == None:
                    continue
                data = [
                    {
                        'name': d['track'].get('name'),
                        'played_at': d.get('played_at'),
                        'album_name': d['track']['album'].get('name'),
                        'artist_name' : get_artist_name(d)
                    } for d in songs
                ]
                df = pd.DataFrame(data)
                df_list.append(df)
                
                time_stamp -= jump
            
            # storing df to postgres
            if len(df) != 0:
                # add user_id col
                df['user_id'] = 1
                try:
                    postgres_hook = PostgresHook(postgres_conn_id="spotify_etl")
                    conn = postgres_hook.get_conn
                    
                    engine = create_engine('postgresql+psycopg2://', creator=conn)
                    
                    print(type(engine))
                    print(len(df))
                    df.to_sql(
                        name='history',
                        con=engine,
                        if_exists='append',
                        index=False  
                    )
                    return 0
                except Exception as e:
                    print(e)
                    return 1
                
        print("Running Daily Task")
        get_songs_for_all_day()


    [create_history_table] >> load_songs()

dag = process_listening_history()