import json
import requests

def get_tasks_and_hours():
    # Load secrets from file
    with open('SECRET.json') as file:
        data = json.load(file)

    # Extract secret token and database URL
    secret = data['id']
    database = data['database']

    # Define the endpoint URL for listing database pages (i.e., your tasks)
    url = f"https://api.notion.com/v1/databases/{database}/query"

    # Set up headers for the request
    headers = {
        "Authorization": f"Bearer {secret}",
        "Notion-Version": "2022-06-28"  # Update the API version if necessary
    }

    # Make a POST request to the endpoint
    response = requests.post(url, headers=headers)

    # Check the status code
    if response.status_code == 200:
        # Check if the results are empty
        results = response.json().get("results", [])
        if not results:
            print("No tasks retrieved, the database might be empty.")
            return {}
        else:
            # Extract tasks and their hours from the results
            tasks_and_hours = {}
            for result in results:
                task_name = result['properties']['Tasks']['title'][0]['plain_text']
                hours_needed = result['properties']['Hours Needed']['number']
                tasks_and_hours[task_name] = hours_needed
            return tasks_and_hours
    else:
        print(f"Failed to retrieve tasks. Status code: {response.status_code}")
        print("Error message:", response.text)
        return {}

if __name__ == "__main__":
    tasks_and_hours = get_tasks_and_hours()
    print("Tasks and Hours Needed:")
    for task, hours in tasks_and_hours.items():
        print(f"{task}: {hours} hours")
