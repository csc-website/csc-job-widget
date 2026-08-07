const jobsContainer = document.getElementById("jobs");

async function loadJobs() {
  try {
    const response = await fetch("jobs.json", {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error("Unable to load jobs.");
    }

    const jobs = await response.json();

    jobsContainer.replaceChildren();

    if (!Array.isArray(jobs) || jobs.length === 0) {
      const message = document.createElement("p");
      message.className = "status";
      message.textContent = "No current job postings are available.";
      jobsContainer.appendChild(message);
      return;
    }

    jobs.slice(0, 5).forEach(job => {
      const article = document.createElement("article");
      article.className = "job";

      const content = document.createElement("div");
      content.className = "job-content";

      if (job.company_logo_url) {
        const logo = document.createElement("img");
        logo.className = "job-logo";
        logo.src = job.company_logo_url;
        logo.alt = job.employer ? `${job.employer} logo` : "Company logo";
        logo.loading = "lazy";

        content.appendChild(logo);
      }

      const details = document.createElement("div");
      details.className = "job-details";

      const title = document.createElement("a");
      title.className = "job-title";
      title.href = job.link;
      title.target = "_blank";
      title.rel = "noopener noreferrer";
      title.textContent = job.title || "Job opportunity";

      const employer = document.createElement("div");
      employer.className = "employer";
      employer.textContent = job.employer || "";

      details.appendChild(title);
      details.appendChild(employer);

      content.appendChild(details);

      article.appendChild(content);

      jobsContainer.appendChild(article);
    });
  } catch (error) {
    jobsContainer.replaceChildren();

    const message = document.createElement("p");
    message.className = "error";
    message.textContent = "Job listings are temporarily unavailable.";

    jobsContainer.appendChild(message);
  }
}

loadJobs();
