import os
from github import Github
import datetime
from modules.baselineLogging import log
from argparse import ArgumentParser
import json

def check_github():
    return 'GITHUB_ACTIONS' in os.environ

def get_org_name(github_repository):
    if '/' in github_repository:
        return github_repository.split('/')[0]
    else:
        log("Invalid GITHUB_REPOSITORY format: %s Expected 'owner/repo'." % github_repository, 'ERROR')

def load_arguments(org_name, commit_msg, repo_name, github_ref_name):
    parser = ArgumentParser()
    parser.add_argument("-t", "--token", required=True,
                        help="Github Access Token")
    parser.add_argument("-r", "--repo", default=(org_name + "/veracode-baseline"), \
                        help="Name of the repository where the baseline will be stored. Example: wasptree/veracode-baseline")
    parser.add_argument("-p", "--policy", default=True,
                        help="Specify whether Policy scan results should be downloaded")
    parser.add_argument("-f", "--file", default="results.json",
                        help="Specify the name of the results/baseline file (json) to read in")
    parser.add_argument("-c", "--commit", default=commit_msg,
                        help="Custom commit message")
    parser.add_argument("-a", "--appname", default=repo_name,
                        help="Specify the appname, used to download policy-to-baseline from Veracode platform")
    parser.add_argument("-b", "--branch", default=github_ref_name,
                        help="Override the default ref, which is the branch name")
    parser.add_argument("-cf", "--checkbf", default=True,
                        help="Check if the baseline file to be pushed is new (less than 10 minutes old)")
    args = parser.parse_args()
    return (
            args.token,
            args.repo,
            args.policy,
            args.file,
            args.commit,
            args.appname,
            args.branch,
            args.checkbf
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
    try:
        # Get the modification time of the file
        modification_time = os.path.getmtime(file)
        # Get the current time
        current_time = datetime.time()
        # Calculate the time difference in seconds
        time_difference = current_time - modification_time
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
        with open(output_path, 'w') as file:
            file.write(file_content)

        return True
    except Exception as e:
        log(f"Error downloading file from repository: {e}", 'ERROR')
        return False

def dummy_baseline(file):
    log("No baseline file retrieved - creating Dummy baseline.json", 'INFO')
    json_data = {
    "findings": []
    }
    
    with open(file, 'w') as file:
        json.dump(json_data, file)
    

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

    # extract the org name
    org_name = get_org_name(github_repository)

    commit_message = "Veracode baseline file update from repo: %s branch: %s pipeline: %s" \
        % (github_repository, github_ref_name, github_run_id) 

    # load arguments
    (
    token,
    repo,
    policy,
    file,
    commit_message,
    appname,
    branch,
    check_baseline
    ) = load_arguments(org_name, commit_message, github_repository, github_ref_name)

    # Specify the path structure for the baseline files
    target_path = repo + "/" + branch + "/" + "baseline.json"

    # Check if running on PR, if so attempt to download a baseline file
    # If not PR attempt to upload a baseline file
    if is_pull_request_event():
        if not download_baseline_file(token, repo, target_path, "baseline.json") and not os.path.exists(file):
            # If no baseline file , create a dummy to avoid pipeline scan failure
            dummy_baseline
        
    else:
        if check_baseline:
            if check_baseline_file_age(file):
                push_baseline_update(token, repo, file, target_path, commit_message)
            else:
                log("Baseline file does not appear to be new - skipping baseline update", 'WARN')
            

