import json

from airflow.providers.postgres.hooks.postgres import PostgresHook

from airflow.models import Variable

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from jinja2 import Environment, BaseLoader

def send_wrapped_email(**context):
    postgres_hook = PostgresHook(postgres_conn_id="spotify_etl")
    ti = context['ti']
    wrapped, email = ti.xcom_pull(task_ids='generate_wrapped')
    print(wrapped, email)

    # load template
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()

    template_query = "select template from templates where name='wrapped_template';"
    cursor.execute(template_query)
    template = cursor.fetchall()[0][0]

    rtemplate = Environment(loader=BaseLoader()).from_string(template)
    data = rtemplate.render(
        wrapped=json.loads(wrapped)
    )
    
    message = Mail(
        from_email='me@ganeshfutane.in',
        to_emails=email,
        subject='Here Is Your Weekly Wrapped!!',
        html_content=data)
    try:
        sg = SendGridAPIClient(Variable.get('EMAIL_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print("ERROR!!!")

def generate_wrapped():
    postgres_hook = PostgresHook(postgres_conn_id="spotify_etl")
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()
    top_artist_query =  """
        select artist_name, count(artist_name) as count 
            FROM history 
            WHERE played_at > CURRENT_DATE - 7 
            GROUP BY artist_name 
            ORDER BY count 
            DESC 
            LIMIT 3;
    """

    cursor.execute(top_artist_query)
    desc = cursor.description
    cols = [c[0] for c in desc]
    data = [dict(zip(cols, row)) for row in cursor.fetchall()]

    print(data)

    json_data = json.dumps(data)
    print(json_data)

    email_query = 'SELECT email from users WHERE id=1'
    cursor.execute(email_query)
    email = cursor.fetchall()

    
    # store this in wrapped ==> persistence

    store_wrapped_query = f"INSERT INTO weekly_wrapped (user_id, wrapped) VALUES (1, '{json_data}');"
    cursor.execute(store_wrapped_query)

    conn.commit()
    conn.close() 

    return json_data, email[0][0]