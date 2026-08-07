const jobsContainer = document.getElementById("jobs");

async function loadJobs() {
  try {
    const response = await fetch("jobs.json", { cache: "no-store" });
    if (!response.ok) throw new Error("Unable to load jobs.");
    const jobs = await response.json();

    jobsContainer.replaceChildren();

    if (!Array.isArray(jobs) || jobs.length === 0) {
      const p = document.createElement("p");
      p.className = "status";
      p.textContent = "No current job postings are available.";
      jobsContainer.appendChild(p);
      return;
    }

    jobs.slice(0, 5).forEach(job => {
      const article = document.createElement("article");
      article.className = "job";

      const title = document.createElement("a");
      title.className = "job-title";
      title.href = job.link;
      title.target = "_blank";
      title.rel = "noopener noreferrer";
      title.textContent = job.title || "Job opportunity";

      const employer = document.createElement("div");
      employer.className = "employer";
      employer.textContent = job.employer || "";

      const view = document.createElement("a");
      view.className = "view-job";
      view.href = job.link;
      view.target = "_blank";
      view.rel = "noopener noreferrer";
      view.textContent = "View job";

      article.append(title, employer, view);
      jobsContainer.appendChild(article);
    });
  } catch (error) {
    jobsContainer.replaceChildren();
    const p = document.createElement("p");
    p.className = "error";
    p.textContent = "Job listings are temporarily unavailable.";
    jobsContainer.appendChild(p);
  }
}

loadJobs();
