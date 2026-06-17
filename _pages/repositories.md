---
layout: page
permalink: /repositories/
title: repositories
description: Open-source repositories and projects
nav: true
nav_order: 4
---

<div id="repos" class="repositories d-flex flex-wrap flex-md-row flex-column justify-content-between align-items-center">
</div>

<script>
const LANG_COLORS = {
  "Julia": "#a270ba",
  "JavaScript": "#f1e05a",
  "TypeScript": "#3178c6",
  "Python": "#3572A5",
  "C#": "#178600",
  "C++": "#f34b7d",
  "C": "#555555",
  "HTML": "#e34c26",
  "CSS": "#563d7c",
  "SCSS": "#c6538c",
  "Shell": "#89e051",
  "Rust": "#dea584",
  "Go": "#00ADD8",
  "MATLAB": "#e16737",
  "TeX": "#3D6117",
  "Jupyter Notebook": "#DA5B0B",
};

async function loadRepos() {
  const container = document.getElementById("repos");
  try {
    const users = {{ site.data.repositories.github_users | jsonify }};
    for (const user of users) {
      const res = await fetch(`https://api.github.com/users/${user}/repos?per_page=100&sort=pushed`);
      if (!res.ok) throw new Error(`GitHub API error: ${res.status}`);
      const repos = await res.json();

      repos
        .filter(r => !r.fork)
        .sort((a, b) => b.stargazers_count - a.stargazers_count || new Date(b.pushed_at) - new Date(a.pushed_at))
        .forEach(repo => {
          const langDot = repo.language
            ? `<span class="lang-dot" style="background:${LANG_COLORS[repo.language] || '#888'}"></span> ${repo.language}`
            : "";
          const desc = repo.description || "";
          container.insertAdjacentHTML("beforeend", `
            <div class="repo p-2">
              <a href="${repo.html_url}">
                <div class="repo-card">
                  <h6>${repo.name}</h6>
                  <p>${desc}</p>
                  <div class="repo-meta">
                    <span>${langDot}</span>
                    <span>&#9733; ${repo.stargazers_count}</span>
                    <span>&#9906; ${repo.forks_count}</span>
                  </div>
                </div>
              </a>
            </div>
          `);
        });
    }
  } catch (e) {
    container.innerHTML = `<p>Failed to load repositories. <a href="https://github.com/${users[0]}">View on GitHub</a>.</p>`;
  }
}
loadRepos();
</script>
