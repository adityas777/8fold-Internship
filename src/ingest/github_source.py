import requests
from typing import List, Tuple, Any

def extract(username_or_url: str) -> List[Tuple[str, str, Any, str, str]]:
    """
    Queries public GitHub REST API for candidate's profile and repositories.
    Extracts name, location, blog link, github url, bio, and repository languages as skills.
    """
    results = []
    
    # Extract username from URL if necessary
    username = username_or_url.strip()
    if "/" in username:
        username = username.split('/')[-1]
        
    if not username:
        return results

    source_name = "github"
    method = "github_api"
    record_id = f"github_{username}"

    headers = {
        "User-Agent": "Eightfold-Profile-Pipeline-Agent"
    }

    # Fetch User Profile
    user_url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(user_url, headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            
            # Name
            name = user_data.get("name")
            if name:
                results.append((record_id, "full_name", name.strip(), source_name, method))
            
            # Email
            email = user_data.get("email")
            if email:
                results.append((record_id, "emails", [email.strip()], source_name, method))
            
            # Location
            loc = user_data.get("location")
            if loc:
                results.append((record_id, "location", loc.strip(), source_name, method))
                
            # Links (GitHub Profile HTML URL)
            html_url = user_data.get("html_url")
            blog = user_data.get("blog")
            links = []
            if html_url:
                links.append(html_url)
            if blog:
                links.append(blog)
            if links:
                results.append((record_id, "links", links, source_name, method))
                
            # Headline / Bio
            bio = user_data.get("bio")
            if bio:
                results.append((record_id, "headline", bio.strip(), source_name, method))
        elif response.status_code == 403:
            print(f"Warning: GitHub API rate limited when querying user {username}")
        elif response.status_code == 404:
            print(f"Warning: GitHub user {username} not found")
    except Exception as e:
        print(f"Error querying GitHub user API for {username}: {e}")

    # Fetch Repos to extract language skills
    repos_url = f"https://api.github.com/users/{username}/repos"
    try:
        response = requests.get(repos_url, headers=headers, timeout=10)
        if response.status_code == 200:
            repos_data = response.json()
            languages = set()
            for repo in repos_data:
                lang = repo.get("language")
                if lang:
                    languages.add(lang.strip())
            
            if languages:
                results.append((record_id, "skills", list(languages), source_name, method))
        elif response.status_code == 403:
            print(f"Warning: GitHub API rate limited when querying repos for {username}")
    except Exception as e:
        print(f"Error querying GitHub repos API for {username}: {e}")

    return results
