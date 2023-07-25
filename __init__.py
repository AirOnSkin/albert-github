# -*- coding: utf-8 -*-

"""
This plugin searches GitHub user repositories and opens the selected match in the browser.
Trigger with 'gh '.
Refresh cache with 'gh refresh cache'.
"""

import os
import json
from albert import *
from github import Github
from rapidfuzz import fuzz

md_iid = '1.0'
md_version = "0.1"
md_name = "GitHub repositories"
md_description = "Open GitHub user repositories in the browser"
md_license = "GPL-3.0"
md_url = "https://github.com/aironskin/albert-github"
md_maintainers = "@aironskin"
md_lib_dependencies = ["github", "rapidfuzz"]

plugin_dir = os.path.dirname(__file__)
TOKEN_FILE = os.path.join(plugin_dir, "github_token.txt")
CACHE_FILE = os.path.join(plugin_dir, "repository_cache.json")

class Plugin(TriggerQueryHandler):

  icon = [os.path.dirname(__file__) + "/plugin.svg"]

  def id(self):
    return md_id

  def name(self):
    return md_name

  def description(self):
    return md_description

  def defaultTrigger(self):
    return "gh "

  def save_token(self, token):
    # Save the token in a file
    with open(TOKEN_FILE, "w") as file:
      file.write(token)

  def load_token(self):
    # Load the token from the file if it exists
    if os.path.exists(TOKEN_FILE):
      with open(TOKEN_FILE, "r") as file:
        return file.read().strip()
    return None

  def get_user_repositories(self, token):
    # Fetch user repositories from GitHub using the provided token
    g = Github(token)
    user = g.get_user()
    repositories = []
    for repo in user.get_repos():
      repositories.append(
        {
          "name": repo.name,
          "full_name": repo.full_name,
          "html_url": repo.html_url,
        }
      )
    return repositories

  def cache_repositories(self, repositories):
    # Cache the repositories on the file system
    with open(CACHE_FILE, "w") as file:
      json.dump(repositories, file)

  def load_cached_repositories(self):
    # Load the cached repositories from the file if it exists
    if os.path.exists(CACHE_FILE):
      with open(CACHE_FILE, "r") as file:
        return json.load(file)
    return None

  def fuzzy_search_repositories(self, repositories, search_string):
    # Perform fuzzy search on the repositories
    matching_repos = []
    for repo in repositories:
      repo_name = repo["name"]
      ratio = fuzz.token_set_ratio(repo_name.lower(), search_string.lower())
      if ratio >= 75:
        matching_repos.append(repo)
    return matching_repos

  def handleTriggerQuery(self, query):

    # Load GitHub user token
    token = self.load_token()
    if not token:
      query.add(Item(id=md_id,
                     text=md_name,
                     icon=self.icon,
                     subtext="Paste your GitHub token and press [enter] to save it",
                     actions=[Action("save", "Save token", lambda t=query.string.strip(): self.save_token(t))]))

    # Load the repositories from cache or fetch them from GitHub
    repositories = self.load_cached_repositories()
    if not repositories:
      query.add(Item(id=md_id,
                     text=md_name,
                     icon=self.icon,
                     subtext="Press [enter] to initialize the repository cache (may take a few seconds)",
                     actions=[Action("cache", "Create repository cache", lambda: self.cache_repositories(self.get_user_repositories(token)))]))

    query_stripped = query.string.strip()

    if query_stripped:

      # Refresh local repositories cache
      if query_stripped.lower() == "refresh cache":
        query.add(Item(id=md_id,
                       text=md_name,
                       icon=self.icon,
                       subtext="Press [enter] to refresh the local repository cache (may take a few seconds)",
                       actions=[Action("refresh", "Refresh repository cache", lambda: self.cache_repositories(self.get_user_repositories(token)))]))

      if not repositories:
        return []

      # Fuzzy search the query in repository names
      search_term = query.string.strip().lower()
      exact_matches = []
      fuzzy_matches = []

      for repo in repositories:
        repo_name = repo["name"]
        if repo_name.lower().startswith(search_term):
          exact_matches.append(repo)
        else:
          similarity_ratio = fuzz.token_set_ratio(repo_name.lower(), search_term)
          if similarity_ratio > 25:
            fuzzy_matches.append((repo, similarity_ratio))

      # Sort the fuzzy matches based on similarity ratio
      fuzzy_matches.sort(key=lambda x: x[1], reverse=True)

      results = []
      for repo in exact_matches:
        results.append(Item(id=md_id,
                            text=repo["name"],
                            icon=self.icon,
                            subtext=repo["full_name"],
                            actions=[Action("eopen", "Open exact match", lambda u=repo["html_url"]: openUrl(u))]))

      for repo, similarity_ratio in fuzzy_matches:
        results.append(Item(id=md_id,
                            text=repo["name"],
                            icon=self.icon,
                            subtext=repo["full_name"],
                            actions=[Action("fopen", "Open fuzzy match", lambda u=repo["html_url"]: openUrl(u))]))

      if results:
        query.add(results)
      else:
        query.add(Item(id=md_id,
                       text="No repositories matching search string",
                       icon=self.icon))

    else:
      query.add(Item(id=md_id,
                     icon=self.icon,
                     text="...",
                     subtext="Search for a GitHub user repository name"))
