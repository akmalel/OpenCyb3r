def update_readme(leaderboard, repo):
    top_5 = leaderboard[:5]
    markdown = f"# {repo} Top 5 Contributors\n\n"
    markdown += "| Rank | Contributor | Contributions |\n"
    markdown += "|------|-------------|----------------|\n"
    for rank, contributor in enumerate(top_5, start=1):
        markdown += (
            f"| {rank} | "
            f"<img src='{contributor['avatar_url']}' alt='{contributor['username']}' width='40'> "
            f"{contributor['username']} | {contributor['contributions']} |\n"
        )

    try:
        with open("README.md", "r") as file:
            content = file.readlines()

        with open("README.md", "w") as file:
            updated = False
            for line in content:
                if line.strip() == "<!-- LEADERBOARD START -->":
                    file.write("<!-- LEADERBOARD START -->\n")
                    file.write(markdown)
                    file.write("\n<!-- LEADERBOARD END -->\n")
                    updated = True
                elif not (line.strip() == "<!-- LEADERBOARD END -->"):
                    file.write(line)

            if not updated:
                file.write("\n<!-- LEADERBOARD START -->\n")
                file.write(markdown)
                file.write("\n<!-- LEADERBOARD END -->\n")

        print("README.md updated successfully with the Top 5 leaderboard.")
    except FileNotFoundError:
        print("README.md not found. Creating a new one.")
        with open("README.md", "w") as file:
            file.write(markdown)
