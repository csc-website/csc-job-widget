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

    jobs.slice(0, 5).forEach(function(job) {
      var article = document.createElement("article");
      article.className = "job";

      var content = document.createElement("div");
      content.className = "job-content";

      if (job.company_logo_url) {
        var logo = document.createElement("img");

        logo.className = "job-logo";
        logo.src = job.company_logo_url;
        logo.alt = job.employer
          ? job.employer + " logo"
          : "Company logo";
        logo.loading = "lazy";

        logo.addEventListener("error", function() {
          logo.style.display = "none";
        });

        content.appendChild(logo);
      }

      var details = document.createElement("div");
      details.className = "job-details";

      var title = document.createElement("a");
      title.className = "job-title";
      title.href = job.link;
      title.target = "_blank";
      title.rel = "noopener noreferrer";
      title.textContent = job.title || "Job opportunity";

      var employer = document.createElement("div");
      employer.className = "employer";
      employer.textContent = job.employer || "";

      var viewJob = document.createElement("a");
      viewJob.className = "view-job";
      viewJob.href = job.link;
      viewJob.target = "_blank";
      viewJob.rel = "noopener noreferrer";
      viewJob.textContent = "View Job";

      details.appendChild(title);
      details.appendChild(employer);
      details.appendChild(viewJob);

      content.appendChild(details);
      article.appendChild(content);

      jobsContainer.appendChild(article);
    });

  } catch (error) {
    console.error("Jobs widget error:", error);

    jobsContainer.replaceChildren();

    var message = document.createElement("p");
    message.className = "error";
    message.textContent = "Job listings are temporarily unavailable.";

    jobsContainer.appendChild(message);
  }
}

loadJobs();
