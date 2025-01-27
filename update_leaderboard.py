import requests
import json
import argparse
import re

def get_contributors(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    response = requests.get(url)

    if response.status_code == 200:
        contributors = response.json()
        leaderboard = []

        for contributor in contributors:
            leaderboard.append({
                "username": contributor["login"],
                "contributions": contributor["contributions"],
                "avatar_url": contributor["avatar_url"]
            })

        # Ensure the repo owner is included in the leaderboard
        repo_info_url = f"https://api.github.com/repos/{owner}/{repo}"
        repo_info_response = requests.get(repo_info_url)
        if repo_info_response.status_code == 200:
            repo_info = repo_info_response.json()
            owner_username = repo_info["owner"]["login"]
            owner_avatar_url = repo_info["owner"]["avatar_url"]

            # Check if the owner is already in the contributors list
            if not any(c["username"] == owner_username for c in leaderboard):
                leaderboard.append({
                    "username": owner_username,
                    "contributions": 0,  # Default to 0 contributions if not listed
                    "avatar_url": owner_avatar_url
                })

        return sorted(leaderboard, key=lambda x: x["contributions"], reverse=True)
    else:
        print(f"Failed to fetch contributors: {response.status_code}")
        return []

def generate_html(leaderboard, owner, repo):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{repo} Leaderboard</title>
        <style>
            body {{ 
                background: linear-gradient(0deg, #1b2838, #1e3a4c, #1f4c60, #16202b);
                background-size: 300% 300%;
                animation: gradient 30s ease infinite;
                font-family: Arial, sans-serif; 
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
                overflow: hidden;
            }}

            @keyframes gradient {{
                0% {{
                    background-position: 50% 0%;
                }}
                50% {{
                    background-position: 50% 100%;
                }}
                100% {{
                    background-position: 50% 0%;
                }}
            }}

            table {{ border-collapse: collapse; width: 80%; margin-top: 20px; z-index: 1; position: relative; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .avatar {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                margin-right: 10px;
                vertical-align: middle;
            }}
            h1 {{
                color: white;
                text-align: center;
                margin-top: 20px;
                z-index: 1;
                position: relative;
            }}
        </style>
    </head>
    <body>
        <h1>OpenCyb3r Leaderboard</h1>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Contributor</th>
                    <th>Contributions</th>
                </tr>
            </thead>
            <tbody>
    """
    for rank, contributor in enumerate(leaderboard, start=1):
        html += f"""
                <tr>
                    <td>{rank}</td>
                    <td><img src='{contributor['avatar_url']}' alt='Avatar' class='avatar'>{contributor['username']}</td>
                    <td>{contributor['contributions']}</td>
                </tr>
        """
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

def save_html_to_file(html, filename="leaderboard.html"):
    with open(filename, "w") as file:
        file.write(html)

import re

def update_readme(leaderboard, repo):
    top_5 = leaderboard[:5]
    markdown = f"# {repo} Top 5 Contributors\n\n"
    markdown += "| Rank | Contributor | Contributions |\n"
    markdown += "|------|-------------|----------------|\n"
    for rank, contributor in enumerate(top_5, start=1):
        markdown += (
            f"| {rank} | "
            f"<img src='{contributor['avatar_url']}' alt='{contributor['username']}' width='20' height='20'> "
            f"{contributor['username']} | {contributor['contributions']} |\n"
        )

    start_marker = "<!-- LEADERBOARD START -->"
    end_marker = "<!-- LEADERBOARD END -->"
    leaderboard_section = f"{start_marker}\n{markdown}\n{end_marker}"

    try:
        with open("README.md", "r") as file:
            content = file.read()

        # Replace or append the leaderboard section
        if start_marker in content and end_marker in content:
            # Replace the content between the markers
            updated_content = re.sub(
                f"{start_marker}.*?{end_marker}",
                leaderboard_section,
                content,
                flags=re.DOTALL,
            )
        else:
            # Add markers and leaderboard if missing
            updated_content = f"{content.strip()}\n\n{leaderboard_section}\n"

        with open("README.md", "w") as file:
            file.write(updated_content)

        print("README.md updated successfully with the Top 5 leaderboard.")
    except FileNotFoundError:
        print("README.md not found. Creating a new one.")
        with open("README.md", "w") as file:
            file.write(leaderboard_section)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update leaderboard.')
    parser.add_argument('--owner', required=True, help='The GitHub repository owner')
    parser.add_argument('--repo', required=True, help='The GitHub repository name')
    args = parser.parse_args()

    owner = args.owner
    repo = args.repo

    print("Generating GitHub repository leaderboard...")

    leaderboard = get_contributors(owner, repo)

    if leaderboard:
        html = generate_html(leaderboard, owner, repo)
        save_html_to_file(html)
        update_readme(leaderboard, repo)
        print("Leaderboard HTML and README updated successfully.")
    else:
        print("No contributors found or failed to retrieve data.")
