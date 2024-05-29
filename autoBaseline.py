import os
from github import Github
from datetime import datetime
from modules.baselineLogging import log
from argparse import ArgumentParser
import json

TEMP_DIRECTORY = ".veracode-autobaseline"
BASELINE_FILE = "baseline.json"

def check_github():
    return 'GITHUB_ACTIONS' in os.environ

def get_org_name(github_repository):
    if '/' in github_repository:
        return github_repository.split('/')[0]
    else:
        log("Invalid GITHUB_REPOSITORY format: %s Expected 'owner/repo'." % github_repository, 'ERROR')

def get_repo_name(github_repository):
    if '/' in github_repository:
        return github_repository.split('/')[1]
    else:
        log("Invalid GITHUB_REPOSITORY format: %s Expected 'owner/repo'." % github_repository, 'ERROR')

def load_arguments():

    (
    github_base_ref,
    github_ref,
    github_repository,
    github_sha,
    github_run_id,
    github_ref_name
    ) = get_github_variables()

    org_name = get_org_name(github_repository)

    commit_msg = "Veracode baseline file update from repo: %s branch: %s pipeline: %s" \
    % (github_repository, github_ref_name, github_run_id)
    
    parser = ArgumentParser()
    parser.add_argument("-t", "--token", required=True,
                        help="Github Access Token")
    parser.add_argument("-s", "--source",
                        help="Name of the repository where the baseline files will be stored. Default : <owner>/veracode-baseline")
    parser.add_argument("-f", "--file",
                        help="Specify the name of the results/baseline file (json) to read in. | Default : results.json")
    parser.add_argument("-c", "--commit",
                        help="Custom commit message")
    parser.add_argument("-b", "--branch",
                        help="Override the default ref, which is the branch name | Default is GITHUB_BASE_REF ")
    parser.add_argument("-r", "--repo",
                        help="Override the name of the owner/project for storage. | Default is GITHUB_REPOSITORY ")
    parser.add_argument("-cf", "--checkbf",
                        help="Check if the baseline file to be pushed is new (less than 10 minutes old) | Default is True")
    parser.add_argument("-u", "--update",
                        help="Used to update the baseline file in the repository, run after scan. | Default is False")
    args = parser.parse_args()

    if args.file == "":
        args.file = "results.json"
    if args.source == "":
        args.source = (org_name + "/veracode-baseline")
    if args.commit == "":
        args.commit = commit_msg
    if args.branch == "":
        args.branch = github_base_ref
    if args.repo == "":
        args.repo = github_repository
    if args.checkbf == "":
        args.checkbf = True
    else:
        args.checkbf = bool(args.checkbf)
    if args.update == "":
        args.update = False
    else:
        args.update = bool(args.update)

    return (
            args.token,
            args.source,
            args.file,
            args.commit,
            args.branch,
            args.repo,
            args.checkbf,
            args.update
            )


# Function to check if the environment is a pull_request event
def is_pull_request_event():
    return os.getenv('GITHUB_EVENT_NAME') == 'pull_request'

# Function to grab the Github variables, used to store and lookup the required baseline file
def get_github_variables():
    github_base_ref = os.getenv('GITHUB_BASE_REF')
    github_ref = os.getenv('GITHUB_REF')
    github_repository = os.getenv('GITHUB_REPOSITORY')
    github_sha = os.getenv('GITHUB_SHA')
    github_run_id = os.getenv('GITHUB_RUN_ID')
    github_ref_name = os.getenv('GITHUB_REF_NAME')

    return (github_base_ref,
            github_ref,
            github_repository,
            github_sha,
            github_run_id,
            github_ref_name)

def push_file_to_repo(token, repo_name, file_path, file_content, commit_message):
    # Authenticate with your GitHub token
    g = Github(token)
    
    # Get the repository
    repo = g.get_repo(repo_name)
    
    # Create a new file in the repository
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(file_path, commit_message, file_content, contents.sha)
    except:
        repo.create_file(file_path, commit_message, file_content)
    
    log("File pushed successfully!", 'INFO')

def load_baseline(filename):
    try:
        with open(filename, 'r') as file:
            contents = file.read()
        return contents
    except FileNotFoundError:
        log(f"File '{filename}' not found.", 'ERROR')
        return None
    except Exception as e:
        log(f"Error reading file '{filename}': {e}", 'ERROR')
        return None

def push_baseline_update(token, repo, baseline_file, target_path, commit_message,):
    baseline_contents = load_baseline(baseline_file)

    # Call the function to push the file to the remote repository
    push_file_to_repo(token, repo, target_path, baseline_contents, commit_message)

def check_baseline_file_age(file):
    log("Checking the age of the local results.json file", 'INFO')
    try:
        # Get the modification time of the file
        modification_time = os.path.getmtime(file)
        modification_datetime = datetime.fromtimestamp(modification_time)
        # Get the current time
        current_datetime = datetime.now()
        # Calculate the time difference in seconds
        time_difference = (current_datetime - modification_datetime).total_seconds()
        # Check if the time difference is less than 10 minutes old
        if time_difference < 600:
            return True
    except FileNotFoundError:
        log(f"File '{file}' not found.", 'ERROR')
        return False
    except Exception as e:
        log(f"Error checking file '{file}': {e}", 'ERROR')
        return False

def download_baseline_file(access_token, repo_name, file_path, output_path):
    log(f"Attempting to download baseline file from: {repo_name}/{file_path}", 'INFO')
    try:
        # Authenticate with GitHub using the access token
        g = Github(access_token)
        
        # Get the repository
        repo = g.get_repo(repo_name)

        # Get the file contents
        contents = repo.get_contents(file_path)

        # Decode the file content from base64
        file_content = contents.decoded_content.decode()

        # Write the content to the output file

        check_temp_directory(output_path)
        
        with open(output_path, 'w') as file:
            file.write(file_content)

        return True
    except Exception as e:
        log(f"Error downloading file from repository: {file_path} {e}", 'WARN')
        return False

def dummy_baseline(file):
    log("No baseline file retrieved - creating Dummy baseline.json", 'INFO')
    json_data = {
    "findings": []
    }
    
    check_temp_directory(file)

    with open(file, 'w') as f:
        json.dump(json_data, f)

def check_temp_directory(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
def is_valid_json(file):
    try:
        with open(file, 'r') as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, FileNotFoundError) as e:
        log(f"Error checking file '{file}': {e}", 'ERROR')
        return False

# Example usage
if __name__ == "__main__":

    #Check that we are executing within a Github action
    if not check_github():
        log("Not executing within a Github action - Exiting", 'ERROR')
        exit(1)

    #Grab environment variables from pipeline
    (
    github_base_ref,
    github_ref,
    github_repository,
    github_sha,
    github_run_id,
    github_ref_name
    ) = get_github_variables()

    # load arguments
    (
    token,
    source,
    file,
    commit,
    branch,
    repo,
    check_baseline,
    update
    ) = load_arguments()

    # split out the repo name
    repo_name = get_repo_name(repo)

    # Specify the path structure for the baseline files
    target_path = repo_name + "/" + branch + "/" + "baseline.json"
    temp_directory = TEMP_DIRECTORY + "/"
    output_file = temp_directory + BASELINE_FILE

    # Check if running on PR, if so attempt to download a baseline file
    # If not PR attempt to upload a baseline file
    if is_pull_request_event():
        if not download_baseline_file(token, source, target_path, output_file) and not os.path.exists(output_file):
            # If no baseline file , create a dummy to avoid pipeline scan failure
            dummy_baseline(output_file)
        is_valid_json(output_file)
    #Check that the baseline file is valid Json before continuing
    elif update:
        if check_baseline:
            if check_baseline_file_age(file):
                push_baseline_update(token, repo, file, target_path, commit)
            else:
                log("Baseline file appears to be old - skipping baseline update", 'WARN')
        else:
            push_baseline_update(token, repo, file, target_path, commit)
    else:
        log("Not running in a Pull Request - Skipping", 'INFO')