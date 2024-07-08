from openai import OpenAI
import os

CURRICULUM_PATH = "/Users/annhoward/Library/Mobile Documents/iCloud~md~obsidian/Documents/multiverse_school_curriculum/Curriculum"
client = OpenAI()
curriculum_agent = client.beta.assistants.retrieve("asst_fPqodtkr1MX4OXmPCuBwBkMs")

class_lengths = [
    "20 minutes",
    "1 hour",
    "1 2 hour session",
    "4 1-hour sessions",
    "3 1-hour sessions",
    "5 1-hour sessions",
    "10 1-hour sessions"
]

class_types = [
    "self-study",
    "instructor-led",
    "community-led"
]
topics = [
    "HTML & CSS",
    "JavaScript",
    "Statistics with Python"
]

for topic in topics:
    ## create the folder
    folder_path = os.path.join(CURRICULUM_PATH, topic)
    os.makedirs(folder_path, exist_ok=True)
    
    for class_type in class_types:
        ## create a subfolder for each class type
        class_type_folder_path = os.path.join(folder_path, class_type)
        os.makedirs(class_type_folder_path, exist_ok=True)
        
        for length in class_lengths:
            ## syllabus name is {length} {class_type} {topic} Syllabus.md
            syllabus_file_path = os.path.join(class_type_folder_path, f"{length} {class_type} {topic} Syllabus.md")

            system_prompt = f"""
            You are a curriculum maintainer for The Multiverse School. 
            Your role is to help write {class_type} syllabi for the classes at The Multiverse School. 
            You will be given a class topic, a number of sessions to plan for. 
            Please use the class syllabus to write a {class_type} syllabus for the class. 
            The class syllabus will have a defined sequence of concepts, each with an associated exercise. 
            Each concept will have an article which can be linked to with [[]], for example [[HTML Tags]] or [[Vectors]] or [[If Statements]]. 
            Exercises can be linked similarly [[If Statements Exercise]] or [[Vectors Exercise]]. 
            An article does not need to exist before you link it, only specify what articles should exist. 
            You can link [[words]] in the middle of sentences to specify that article should exist. 
            There is learn to code Python and learn to code Javascript material so if you want to link to an article, specify which language it should be in, for example [[JavaScript - If Statements]] or [[Python - If Statements]]. 
            The link [[must_be_a_valid_unix_filename]] without an extension so you cannot use . or , or : or / or \\ or any other invalid characters. 
            Please review the other syllabus files in the Curriculum folder for examples of how to structure the syllabus. 
            The syllabus should be written in Markdown and any html should be escaped or enclosed in code blocks, or inline code blocks. 
            Please write the full syllabus, and not a template. 
            Only reply with the content for the syllabus, as it will be saved directly to a file and used immediately by a script.
            """
            curriculum_agent.instructions = system_prompt

            thread = client.beta.threads.create()
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Please write a syllabus for a {length} {class_type} course on {topic}."
            )

            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=curriculum_agent.id,
            )

            if run.status == 'completed': 
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                syllabus = messages.data[0].content[0].text.value
                print(messages.data[0].content[0].text.value)
                
                ## write the syllabus to the file
                with open(syllabus_file_path, "w") as f:
                    f.write(syllabus)