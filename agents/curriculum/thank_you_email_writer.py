## we'll run this once a day to make sure registration emails are all written
import os 
import psycopg2
from openai import OpenAI



client = OpenAI()

conn = conn = psycopg2.connect(
            os.environ['DATABASE_URL'],
        )
cur = conn.cursor()



    
## get all the classes in the track so you can figure out the next class, you can use tracks_classes to find all the classses in the same track ID
cur.execute("SELECT track_id, class_id, sequence FROM tracks_classes")
all_track_classes = cur.fetchall()
track_classes = {}
for track_class in all_track_classes:
    if track_class[0] not in track_classes:
        track_classes[track_class[0]] = []
    track_classes[track_class[0]].append((track_class[1], track_class[2]))

classes = []
cur.execute("SELECT id,name FROM classes WHERE post_class_email_template IS NULL")
rows = cur.fetchall()
for row in rows:
    class_info = {
        "id": row[0],
        "name": row[1],
        "classtimes": [],
        "next_class": None,
        "next_class_link": None
    }
    for track in track_classes.keys():
        for class_id, sequence in track_classes[track]:
            if class_id == row[0]:
                current_class_sequence = sequence
                next_class_sequence = sequence + 1
                for next_class_id, next_sequence in track_classes[track]:
                    if next_sequence == next_class_sequence:
                        class_info["next_class"] = next_class_id
                        class_info["next_class_link"] = f"https://themultiverse.school/classes/{next_class_id}"
                        break
    ## now get the first classtime for the class
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
    
    class_prompt = f"Please use the {class_info.get("name")} syllabus to write the thank-you emails for sending to students after the class. Ask students to fill out the feedback form, use this exact link and never use a placeholder: https://forms.gle/5CFpjQsmWepuBc5SA it will always be this link. Please give a short overview of all the homework from the class, encourage students to log into the server if they want help with homework that is not complete, as other multiverse students are there to help. Remind students they can access their Dashboard here: https://themultiverse.school/dashboard. Always include the next class link, which is here (if it says None don't include it as it's the last class in the track): {class_info["next_class_link"]}\n"
    ## get the first class in the next class in the sequence
    ## find the next class from the id in the current class
    next_class_id = class_info.get("next_class")
    if next_class_id:
        for class_info in classes:
            if class_info.get("id") == next_class_id:
                next_class_name = class_info.get("name")
                ## get the first classtime for the class
                for classtime in class_info.get("classtimes"):
                    ## get the first classtime
                    next_class_start_time = classtime.get("start_time")
                    next_class_end_time = classtime.get("end_time")
                    break
                break
        class_prompt += f"\n\nThe next class is {next_class_name} and it will be on {next_class_start_time} - {next_class_end_time}\n"
        
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
        cur.execute("UPDATE classes SET post_class_email_template = %s WHERE id = %s", (email, class_info.get("id")))
        conn.commit()
    else:
        print(run.status)
        
    