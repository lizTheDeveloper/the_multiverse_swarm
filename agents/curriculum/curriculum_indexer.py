from openai import OpenAI
import os

client = OpenAI()


CURRICULUM_PATH = "/Users/annhoward/Library/Mobile Documents/iCloud~md~obsidian/Documents/multiverse_school_curriculum/Curriculum"
PROGRAMS_PATH = "/Users/annhoward/Library/Mobile Documents/iCloud~md~obsidian/Documents/multiverse_school_curriculum/Programs"
SCHOOL_STRUCTURE = "/Users/annhoward/Library/Mobile Documents/iCloud~md~obsidian/Documents/multiverse_school_curriculum/School Structure"


vector_store = client.beta.vector_stores.create(name="curriculum")

def upload_batch(file_paths):
    ## only upload one folder at a time
    file_streams = [open(path, "rb") for path in file_paths]
    
    ## remove any empty files
    file_streams = [f for f in file_streams if os.path.getsize(f.name) > 0]
            
    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    
    while file_batch.status != "completed":
        print(file_batch.status)
        print(file_batch.file_counts)
    print("----------------- Completed -----------------")
    
## recurse over the whole curriculum and index it by it's full path
def index_curriculum(curriculum_path):
    for root, dirs, files in os.walk(curriculum_path):

        # Ready the files for upload to OpenAI
        file_paths = []
        
        ## upload one batch per folder of just the files in that folder
        for d in dirs:
            for f in os.listdir(os.path.join(root, d)):
                if f.endswith(".md"):
                    print(os.path.join(root, d, f), os.path.getsize(os.path.join(root, d, f)))
                    ## if the file is empty, don't add it to the path list
                    
                    if os.path.getsize(os.path.join(root, d, f)) > 0:
                        file_paths.append(os.path.join(root, d, f))
            if len(file_paths) > 0:
                upload_batch(file_paths)
            file_paths = []
        
try: 
    index_curriculum(CURRICULUM_PATH)
    index_curriculum(PROGRAMS_PATH)
    index_curriculum(SCHOOL_STRUCTURE)
except Exception as e:
    print(e)
    ## clean up the vector store
    deleted_vector_store = client.beta.vector_stores.delete(
        vector_store_id=vector_store.id
    )
    print(deleted_vector_store.id + " deleted")
