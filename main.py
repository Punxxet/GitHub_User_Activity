import json
import sys
import urllib.error
import urllib.request

API_URL = "https://api.github.com/users/{username}/events"
TIMEOUT = 10

class GitHubError(Exception):
    """A user-facing problem: bad username, rate limit, no network, etc."""

def fetch_events(username, timeout_sec):
    url = API_URL.format(username = username)
    req = urllib.request.Request(url,headers = {"User-Agent" : "github-user-activity"})

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            data = json.load(response)
            return data

    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise GitHubError(f"GitHub user '{username}' not found ({e.code}).")
        elif e.code == 403 or e.code == 429:
            raise GitHubError(f"Rate limit exceeded or access forbidden ({e.code}).")
        else:
            raise GitHubError(f"GitHub API returned HTTP status {e.code}")
    except TimeoutError:
        raise GitHubError(f"Connection timed out after {timeout_sec} seconds")
    except urllib.error.URLError as e: 
        if isinstance(e.reason,TimeoutError):
            raise GitHubError(f"Connection timed out (wrapped in URLError) after {timeout_sec} seconds.")
        else:
            raise GitHubError(f"Network Failed to connect to GitHub({e.reason}). ")
            
    except json.JSONDecodeError:
        raise GitHubError("GitHub sent a response that isn't valid JSON")
    

def format_event(event):
    event_type = event["type"]
    repo_name = event["repo"]["name"]

    if event_type == "PushEvent":
        branch = event["payload"]["ref"].split("/",2)[-1]
        return f"Pushed to {repo_name} (branch {branch})"
    elif event_type == "CreateEvent":
        ref_type = event["payload"]["ref_type"]
        ref_name = event["payload"]["ref"]

        if ref_type == "repository":
            return f"Created new repository {repo_name}"
        elif ref_type == "branch":
            return f"Created branch '{ref_name}' in {repo_name}"
        elif ref_type == "tag":
            return f"Created tag '{ref_name}' in {repo_name}"
        else:
            return f"Created '{ref_name}' in {repo_name}"
        
    elif event_type == "PullRequestEvent":
        number = event["payload"]["number"]
        action = event["payload"]["action"].capitalize()
        return f"{action} pull request #{number} in {repo_name}"
    
    elif event_type == "ForkEvent":
        return f"Forked {repo_name}"
    else:
        return f"{event_type} in {repo_name}"
    






def main():
    if len(sys.argv) < 2:
        print("Usage: github-activity <username>", file = sys.stderr)
        sys.exit(1)

    username = sys.argv[1].strip()
    try:
        result = fetch_events(username,TIMEOUT)
    except GitHubError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
        

    if not result:
        print(f"No recent activity found for {username}.")
        return
    print(f"Recent activity for {username}")
    for event in result:
        print(f"- {format_event(event)}")

if __name__ == "__main__":
    main()


