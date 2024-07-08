from openai import OpenAI
import os

CURRICULUM_PATH = "/Users/annhoward/Library/Mobile Documents/iCloud~md~obsidian/Documents/multiverse_school_curriculum/Curriculum"
client = OpenAI()
review_agent = client.beta.assistants.retrieve("asst_fPqodtkr1MX4OXmPCuBwBkMs")

def review_syllabus(file_path):
    with open(file_path, "r") as f:
        original_syllabus = f.read()

    review_prompt = """
    You are a curriculum reviewer for The Multiverse School. 
    Your role is to review the provided syllabus and make a list of changes you want to make. 
    The syllabus will be in Markdown format and contain a sequence of concepts, each with an associated exercise. 
    You will provide a list of changes that include correcting any errors, improving clarity, adding or removing content, and ensuring proper structure and linking of articles. 
    Note any places where articles are not linked. 
    Remove any parts that talk about the syllabus, eg 'This syllabus is intended to...' etc. 
    Please review the entire syllabus thoroughly and provide the list of changes as a response only with no other text. 
    Only reply with the changes to the syllabus, as it will be given directly to another language model and used immediately to apply changes to the syllabus.
    """
    review_agent.instructions = review_prompt
    
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=original_syllabus
    )
    
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=review_agent.id,
    )
    
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        changes = messages.data[0].content[0].text.value
        print("Changes to be made:")
        print(changes)
        return changes

def apply_changes_to_syllabus(original_syllabus, changes):
    apply_prompt = "You are a curriculum reviewer for The Multiverse School. Your role is to apply the provided list of changes to the original syllabus. The syllabus will be in Markdown format and contain a sequence of concepts, each with an associated exercise. You will be given the original syllabus and the list of changes to apply. Please add links to articles and exercises throughout the Syllabus that are not present, by adding [[double square braces]] around anything that should link out to articles that are internal to the curriculum, as this will create a file with that name. If you link to a language concept like [[If Statements]] you should instead specify the language, like [[JavaScript If Statements]]. The syllabus should be written in Markdown, with inter-curriculum links expressed with [[double square braces like this]] and any html should be escaped or enclosed in code blocks, or inline code blocks. Only reply with the new syllabus and no other text, as your output will be saved to disk and used immediately by a script. Do not say 'Here is the revised syllabus' or anything similar, just provide the revised syllabus."
    
    review_agent.instructions = apply_prompt
    
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Original Syllabus:\n{original_syllabus}\n\nChanges to apply:\n{changes}"
    )
    
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=review_agent.id,
    )
    
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        revised_syllabus = messages.data[0].content[0].text.value
        return revised_syllabus

def main():
    topics = ["HTML & CSS", "JavaScript", "Statistics with Python"]
    class_types = ["self-study", "instructor-led", "community-led"]
    class_lengths = ["20 minutes", "1 hour", "1 2 hour session", "4 1-hour sessions", "3 1-hour sessions", "5 1-hour sessions", "10 1-hour sessions"]

    for topic in topics:
        folder_path = os.path.join(CURRICULUM_PATH, topic)
        
        for class_type in class_types:
            class_type_folder_path = os.path.join(folder_path, class_type)
            
            for length in class_lengths:
                syllabus_file_path = os.path.join(class_type_folder_path, f"r_{length} {class_type} {topic} Syllabus.md")
                
                if os.path.exists(syllabus_file_path):
                    changes = review_syllabus(syllabus_file_path)
                    with open(syllabus_file_path, "r") as f:
                        original_syllabus = f.read()
                    
                    revised_syllabus = apply_changes_to_syllabus(original_syllabus, changes)
                    
                    revised_file_path = os.path.join(class_type_folder_path, f"r_2 {length} {class_type} {topic} Syllabus.md")
                    with open(revised_file_path, "w") as f:
                        f.write(revised_syllabus)
                    print(f"Revised syllabus saved to: {revised_file_path}")

if __name__ == "__main__":
    main()