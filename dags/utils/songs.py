from airflow.providers.postgres.hooks.postgres import PostgresHook
import json
import requests

from sqlalchemy import create_engine

import time

import pandas as pd
from pandas import json_normalize

from airflow.models import Variable

def refresh_token_before_extract():
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
    return access_token

def get_songs(time_stamp, access_token):
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
        print("Downloaded r")
        data = r.json().get('items')
        return data
    print("Empty Download")
    return None

def get_day_history(**context):
    ti = context['ti']
    token = ti.xcom_pull(task_ids='token_refresh_task')
    time_stamp = int(time.time() * 1e3)
    jump = 7200 

    data = []

    for i in range(12):
        print(f"Getting songs for {time_stamp} slot {i}")
        songs = get_songs(time_stamp, token)

        if songs == None:
            continue

        data.append(songs)

        time_stamp -= jump

    return data

def transform_data(**context):
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract_task')

    df_list = []

    for item in data:
        transformed_data = [
            {
                'name': d['track'].get('name'),
                'played_at': d.get('played_at'),
                'album_name': d['track']['album'].get('name'),
                'artist_name' : get_artist_name(d)
            } for d in item
        ]

        df = pd.DataFrame(transformed_data)

        df_list.append(df)
    final_df = pd.concat(df_list)
    final_df = final_df.drop_duplicates(keep='last')
    json_data = final_df.to_json(orient="records")
    return json_data
        
def get_artist_name(d):
    artist_list = d.get('track').get('artists')
    ls = []
    for a in artist_list:
        ls.append(a.get('name'))
    return ' '.join(ls)

def load_data(**context):
    ti = context['ti']
    tmp = ti.xcom_pull(task_ids='transform_task')
    
    data = json.loads(tmp)
    df = json_normalize(data)
    if len(df) != 0:
        df['user_id'] = 1
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