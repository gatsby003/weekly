import datetime
import json
import pendulum

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python_operator import PythonOperator

from utils.wrapped import generate_wrapped
from utils.wrapped import send_wrapped_email

from airflow.decorators import dag, task


@dag(
    dag_id="weekly_wrapped_dag",
    schedule_interval="0 0 * * 0",
    start_date=pendulum.datetime(2022, 12, 14, tz="UTC"),
    catchup=True,
    dagrun_timeout=datetime.timedelta(minutes=60),
    params={
        "user_id": 1
    }
)
def Generate_Weekly_Wrapped_And_Send_Mail():
    create_wrapped_table= PostgresOperator(
        task_id="create_wrapped_table",
        postgres_conn_id="spotify_etl",
        sql="sql/weekly_wrapped.sql",
    )


    generate_wrapped_task = PythonOperator(
        task_id='generate_wrapped',
        python_callable=generate_wrapped
    )

    send_email = PythonOperator(
        task_id='send_wrapped_email',
        python_callable=send_wrapped_email
    )

    # @task
    # def generate_wrapped():
    #     conn = postgres_hook.get_conn()
    #     cursor = conn.cursor()
    #     top_artist_query =  """
    #         select artist_name, count(artist_name) as count 
    #             FROM history 
    #             WHERE played_at > CURRENT_DATE - 7 
    #             GROUP BY artist_name 
    #             ORDER BY count 
    #             DESC 
    #             LIMIT 3;
    #     """

    #     cursor.execute(top_artist_query)
    #     desc = cursor.description
    #     cols = [c[0] for c in desc]
    #     data = [dict(zip(cols, row)) for row in cursor.fetchall()]

    #     print(data)

    #     json_data = json.dumps(data)
    #     print(json_data)

    #     email_query = 'SELECT email from users WHERE id=1'
    #     cursor.execute(email_query)
    #     email = cursor.fetchall()

        
    #     # store this in wrapped ==> persistence

    #     store_wrapped_query = f"INSERT INTO weekly_wrapped (user_id, wrapped) VALUES (1, '{json_data}');"
    #     cursor.execute(store_wrapped_query)

    #     conn.commit()
    #     conn.close() 

    #     return json_data, email[0][0]
    
    create_wrapped_table >> generate_wrapped_task >> send_email

dag = Generate_Weekly_Wrapped_And_Send_Mail()