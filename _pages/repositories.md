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
  "Julia": "#986DB2",
  "JavaScript": "#FBE251",
  "TypeScript": "#3A8FB7",
  "Python": "#1E88A8",
  "C#": "#1B813E",
  "C++": "#E03C8A",
  "C": "#535953",
  "HTML": "#F05E1C",
  "CSS": "#66327C",
  "SCSS": "#D05A6E",
  "Shell": "#86C166",
  "Rust": "#E1A679",
  "Go": "#2EA9DF",
  "MATLAB": "#F75C2F",
  "TeX": "#42602D",
  "Jupyter Notebook": "#F05E1C",
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
            ? `<span class="lang-dot" style="background:${LANG_COLORS[repo.language] || '#828282'}"></span> ${repo.language}`
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
