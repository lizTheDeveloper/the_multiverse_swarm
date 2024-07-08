## we'll run this once a day to make sure registration emails are all written
import os 
import psycopg2
from openai import OpenAI



client = OpenAI()

conn = conn = psycopg2.connect(
            os.environ['DATABASE_URL'],
        )
cur = conn.cursor()
classes = []

cur.execute("SELECT id,name FROM classes WHERE marketing_email_template IS NULL")
rows = cur.fetchall()
for row in rows:
    class_info = {
        "id": row[0],
        "name": row[1],
        "classtimes": []
    }
    
    cur.execute("SELECT id, start_time, end_time, title, description FROM classtimes WHERE class_id = %s", (row[0],))
    classtimes = cur.fetchall()
    for classtime in classtimes:
        class_info["classtimes"].append({
            "id": classtime[0],
            "start_time": classtime[1].strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": classtime[2].strftime('%Y-%m-%d %H:%M:%S'),
            "title": classtime[3],
            "description": classtime[4]
        })
    classes.append(class_info)
class_registration_email_writer_id = "asst_yEJQp05WHpXz7s9qIjRCfozC"


registration_email_writer = client.beta.assistants.retrieve(class_registration_email_writer_id)

for class_info in classes:

    thread = client.beta.threads.create()
    
    class_prompt = f"Please use the {class_info.get("name")} syllabus to write the registration email for the class.\n"
    
    for classtime in class_info.get("classtimes"):
        class_prompt += f"\nClass Time: {classtime.get("start_time")} - {classtime.get("end_time")}\n"
        class_prompt += f"Title: {classtime.get("title")}\n"
        
    class_prompt += "\n\nDo not use placeholder URLs ever. https://themultiverse.school/dashboard is the student dashboard link. Please defer to the information in the Syllabus over the list above, as only the dates and times are accurate and sometimes the specific order of individual sessions is rearranged in the syllabus but not in the database. Always include times as Pacific and Eastern, they'll be given to you as Pacific times. Do not write the subject or any other text, only include the body of the email alone. The instructor's name is Liz Howard, please sign off with: See you in the future~\n Liz Howard\n\n"

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=class_prompt
    )
    
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=registration_email_writer.id,
    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        print(messages.data[0].content[0].text.value)
        email = messages.data[0].content[0].text.value
        cur.execute("UPDATE classes SET registration_email_template = %s WHERE id = %s", (email, class_info.get("id")))
        conn.commit()
    else:
        print(run.status)
        
    