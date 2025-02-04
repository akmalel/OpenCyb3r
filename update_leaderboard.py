import requests
import os
import re
from datetime import datetime, timedelta

# Use GitHub Secrets or set defaults for repo details
OWNER = os.getenv("REPO_OWNER") or "your_default_owner"
REPO = os.getenv("REPO_NAME") or "your_default_repo"

# XP values for various types of contributions
XP_VALUES = {
    "small_fix": 1,
    "documentation": 2,
    "bug_fix": 3,
    "new_feature": 4,
    "robust_feature": 5
}

def calculate_level(xp):
    """Calculate level based on XP (level up every 50 XP)."""
    return xp // 50

# Keywords to match in commit messages
XP_KEYWORDS = {
    "small_fix": ["typo", "fix", "minor"],
    "documentation": ["docs", "readme", "documentation"],
    "bug_fix": ["bug", "fix issue", "resolve"],
    "new_feature": ["feature", "add", "implement"],
    "robust_feature": ["major", "refactor", "complete module"]
}

def get_commit_dates(owner, repo, username):
    """Fetch the commit dates for a specific contributor."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?author={username}&per_page=100"
    response = requests.get(url)
    if response.status_code == 200:
        commit_data = response.json()
        commit_dates = set()
        for commit in commit_data:
            commit_date = commit["commit"]["author"]["date"].split("T")[0]
            commit_dates.add(commit_date)
        # Return dates sorted (latest first)
        return sorted(commit_dates, reverse=True)
    return []

def calculate_streak(commit_dates):
    """Determine the longest active contribution streak (consecutive days)."""
    if not commit_dates:
        return 0
    streak = 1
    for i in range(len(commit_dates) - 1):
        curr_date = datetime.strptime(commit_dates[i], "%Y-%m-%d").date()
        next_date = datetime.strptime(commit_dates[i + 1], "%Y-%m-%d").date()
        if (curr_date - next_date).days == 1:
            streak += 1
        else:
            break  # streak broken
    return streak

def get_commit_xp(owner, repo, username):
    """
    Fetch commits from GitHub API for the last 90 days and
    calculate XP based on commit messages.
    """
    since_date = (datetime.now() - timedelta(days=90)).isoformat()
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?author={username}&since={since_date}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 0
    commits = response.json()
    xp = 0
    for commit in commits:
        message = commit["commit"]["message"].lower()
        # Count only the first matching category per commit
        for category, keywords in XP_KEYWORDS.items():
            if any(keyword in message for keyword in keywords):
                xp += XP_VALUES[category]
                break
    return xp

def assign_badge(contributions):
    """Assign badge emoji based on the total contribution count."""
    BADGES = {10: "🏅", 50: "🏆", 100: "🥇", 500: "🎖️"}
    # Return the highest badge for which contributions exceed the milestone.
    for milestone in sorted(BADGES.keys(), reverse=True):
        if contributions >= milestone:
            return BADGES[milestone]
    return ""

def get_contributions_last_days(owner, repo, username, days):
    """
    Fetch the number of contributions (commits) in the last 'days' days.
    """
    since_date = (datetime.now() - timedelta(days=days)).isoformat()
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?author={username}&since={since_date}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 0
    commits = response.json()
    return len(commits)

def get_contributors(owner, repo):
    """
    Fetch contributors from the GitHub API and calculate XP, level,
    XP progress, and streak for each (excluding bots).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch contributors: {response.status_code}")
        return []
    
    contributors = response.json()
    leaderboard = []
    for contributor in contributors:
        username = contributor.get("login", "")
        user_type = contributor.get("type", "")
        # Exclude bots
        if "bot" in username.lower() or user_type.lower() == "bot" or username == "github-actions[bot]":
            continue
        xp = get_commit_xp(owner, repo, username)
        level = calculate_level(xp)
        xp_progress = (xp % 50) * 2  # progress percentage (0-100)
        commit_dates = get_commit_dates(owner, repo, username)
        streak = calculate_streak(commit_dates)
        leaderboard.append({
            "username": username,
            "contributions": contributor.get("contributions", 0),
            "avatar_url": contributor.get("avatar_url", ""),
            "level": level,
            "xp_progress": xp_progress,
            "streak": streak,
            "xp": xp
        })
    # Sort contributors by total contributions descending
    return sorted(leaderboard, key=lambda x: x["contributions"], reverse=True)

def generate_html(leaderboard):
    """
    Generate the HTML for the leaderboard with a dark gradient background,
    animated particles, and a welcome modal explaining the XP and streak system.
    """
    # Determine the weekly champion (highest contributions over the last 7 days)
    top_weekly = max(leaderboard, key=lambda x: get_contributions_last_days(OWNER, REPO, x["username"], 7), default=None)
    weekly_champion_html = ""
    if top_weekly:
        weekly_champion_html = f"<h2 style='margin-top: 20px;'>🏆 Weekly Champion: {top_weekly['username']} ({top_weekly['contributions']} contributions)</h2>"
    else:
        weekly_champion_html = "<h2 style='margin-top: 20px;'>🏆 No Weekly Champion Yet</h2>"

    # Build the HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OpenCyb3r Leaderboard</title>
    <style>
        /* Gradient Background & Animation */
        body {{
            background: linear-gradient(-45deg, #050b17, #0d1b2a, #001f3f, #003b64);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            font-family: Arial, sans-serif;
            text-align: center;
            color: white;
            margin: 0;
            padding: 20px;
            overflow: hidden;
            position: relative;
        }}
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        /* Leaderboard Table */
        table {{
            width: 90%;
            margin: 20px auto;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 2px solid #00ffea;
            box-shadow: 0 0 10px #00ffea;
        }}
        th, td {{
            padding: 10px;
            border: 1px solid white;
        }}
        th {{
            background-color: rgba(0, 0, 0, 0.5);
        }}
        tr:hover {{
            background-color: rgba(0, 255, 234, 0.2);
            transition: 0.3s ease-in-out;
        }}

        /* Contributor Avatar */
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
            vertical-align: middle;
            border: 2px solid #00ffea;
            box-shadow: 0 0 10px #00ffea;
        }}

        /* XP Progress Bar */
        .xp-bar {{
            width: 100px;
            height: 10px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            overflow: hidden;
            margin: 0 auto;
        }}
        .xp-progress {{
            height: 100%;
            background: #00ffea;
            transition: width 1s ease-in-out;
        }}

        /* Welcome Modal */
        .modal {{
            display: block;
            position: fixed;
            z-index: 1000;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 15px #00ffea;
        }}
        .modal-content h2 {{
            font-size: 22px;
        }}
        .modal-content p, .modal-content ul {{
            font-size: 14px;
            text-align: left;
        }}
        button {{
            background: #00ffea;
            color: black;
            border: none;
            padding: 8px 15px;
            margin-top: 10px;
            cursor: pointer;
            border-radius: 5px;
            font-weight: bold;
        }}
        button:hover {{
            background: #00ccaa;
        }}

        /* Particle Animation */
        .particle {{
            position: absolute;
            width: 4px;
            height: 4px;
            background-color: rgba(0, 255, 234, 0.8);
            border-radius: 50%;
            opacity: 0.6;
            pointer-events: none;
            animation: moveParticle linear infinite;
        }}
        @keyframes moveParticle {{
            0% {{
                transform: translateY(0px);
                opacity: 1;
            }}
            100% {{
                transform: translateY(-100vh);
                opacity: 0;
            }}
        }}
    </style>
</head>
<body>
    <!-- Welcome Modal -->
    <div id="greetingModal" class="modal">
        <div class="modal-content">
            <h2>Welcome to OpenCyb3r Leaderboard! 👋</h2>
            <p>Earn XP and level up by contributing to the project! Here's how:</p>
            <ul style="text-align:left;">
                <li>📌 Small Fix (Typos, Minor Changes) → +1 XP</li>
                <li>📝 Documentation Improvement → +2 XP</li>
                <li>🐛 Bug Fix → +3 XP</li>
                <li>🚀 New Feature → +4 XP</li>
                <li>🔧 Robust Feature → +5 XP</li>
            </ul>
            <p>🔥 Maintain a contribution streak to climb the leaderboard faster!</p>
            <button onclick="closeModal()">Got it! 🚀</button>
        </div>
    </div>

    <h1>OpenCyb3r Leaderboard</h1>
    {weekly_champion_html}
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Contributor</th>
                <th>Level</th>
                <th>Streak</th>
                <th>XP</th>
                <th>Contributions</th>
            </tr>
        </thead>
        <tbody>
    """
    # Build table rows for each contributor
    for rank, contributor in enumerate(leaderboard, start=1):
        badge = assign_badge(contributor["contributions"])
        html += f"""
            <tr>
                <td>{rank}</td>
                <td>
                    <a href="https://github.com/{contributor['username']}" target="_blank" style="color: #00ffea; text-decoration: none;">
                        <img src="{contributor['avatar_url']}" class="avatar"> {contributor['username']} {badge}
                    </a>
                </td>
                <td>⭐ Level {contributor['level']}</td>
                <td>🔥 {contributor['streak']} days</td>
                <td>
                    <div class="xp-bar">
                        <div class="xp-progress" style="width: {contributor['xp_progress']}%;"></div>
                    </div>
                    {contributor['xp']} XP
                </td>
                <td>{contributor['contributions']}</td>
            </tr>
        """
    html += """
        </tbody>
    </table>

    <!-- Scripts for Modal and Particle Animation -->
    <script>
        function closeModal() {
            document.getElementById("greetingModal").style.display = "none";
        }
        // Ensure the modal is visible on page load
        window.onload = function() {
            setTimeout(function() {
                document.getElementById("greetingModal").style.display = "block";
            }, 500);
        };

        // Create animated particles
        function createParticle() {
            const particle = document.createElement("div");
            particle.classList.add("particle");
            document.body.appendChild(particle);
            particle.style.left = Math.random() * 100 + "vw";
            particle.style.top = Math.random() * 100 + "vh";
            particle.style.animationDuration = Math.random() * 10 + 5 + "s";
            setTimeout(function() {
                particle.remove();
            }, 10000);
        }
        setInterval(createParticle, 200);
    </script>
</body>
</html>
"""
    return html

def save_html_to_file(html, filename="leaderboard.html"):
    """Save the generated HTML to a file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html)

def update_readme(leaderboard):
    """
    Update README.md with the Top 5 contributors while preserving
    other content between markers.
    """
    top_5 = leaderboard[:5]
    leaderboard_section = "\n<!-- LEADERBOARD START -->\n"
    leaderboard_section += "| Rank | Contributor | Contributions |\n"
    leaderboard_section += "|------|-------------|----------------|\n"
    for rank, contributor in enumerate(top_5, start=1):
        leaderboard_section += (
            f"| {rank} | <img src='{contributor['avatar_url']}' width='20' height='20'> {contributor['username']} | {contributor['contributions']} |\n"
        )
    leaderboard_section += "<!-- LEADERBOARD END -->\n"

    try:
        with open("README.md", "r", encoding="utf-8") as file:
            content = file.read()
        if "<!-- LEADERBOARD START -->" in content and "<!-- LEADERBOARD END -->" in content:
            updated_content = re.sub(
                r"<!-- LEADERBOARD START -->.*?<!-- LEADERBOARD END -->",
                leaderboard_section,
                content,
                flags=re.DOTALL
            )
        else:
            updated_content = content.strip() + "\n\n" + leaderboard_section
        with open("README.md", "w", encoding="utf-8") as file:
            file.write(updated_content)
        print("✅ README.md updated successfully.")
    except FileNotFoundError:
        print("⚠️ README.md not found, creating a new one.")
        with open("README.md", "w", encoding="utf-8") as file:
            file.write(leaderboard_section)

if __name__ == "__main__":
    print(f"Generating leaderboard for {OWNER}/{REPO}...")
    leaderboard = get_contributors(OWNER, REPO)
    if leaderboard:
        html_content = generate_html(leaderboard)
        save_html_to_file(html_content)
        print("✅ Leaderboard updated successfully and saved to leaderboard.html.")
        # Uncomment the next line if you wish to update README.md as well.
        # update_readme(leaderboard)
    else:
        print("❌ No contributors found or failed to retrieve data.")
