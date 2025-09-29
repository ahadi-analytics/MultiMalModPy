# Support & Troubleshooting  

If you are  experiencing issues with MultiMalModPy:  
1. Check this documentation and FAQ section below.   
2. Check whether the issue has already been reported on GitHub.   
3. Create a new issue on GitHub.   

<div style="display: flex; gap: 15px; margin: 20px 0;">
  <a href="https://github.com/ahadi-analytics/MultiMalModPy/issues">
    <button class="btn btn-primary btn-lg" type="button">
      View Active Issues
      <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" 
           alt="GitHub Logo" 
           style="width: 20px; height: 20px; vertical-align: middle; margin-left: 8px;">
    </button>
  </a>

  <a href="https://github.com/ahadi-analytics/MultiMalModPy/issues/new/choose">
    <button class="btn btn-primary btn-lg" type="button">
      Report a New Issue
      <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" 
           alt="GitHub Logo" 
           style="width: 20px; height: 20px; vertical-align: middle; margin-left: 8px;">
    </button>
  </a>
</div>

---

## Reporting New Issues

When creating a new issue on GitHub, following these best practices helps the team address your problem quickly:

- **Check for duplicates first:** Make sure the issue hasn’t already been reported.  
- **Use a descriptive title:** Summarize the problem clearly in a few words.  
- **Provide context:** Include MultiMalModPy version, operating system, Python version, and environment (e.g., local or containerized run).  
- **Steps to reproduce:** List the exact commands or steps that led to the issue.  
- **Expected vs. actual behavior:** Describe what you expected to happen and what actually occurred.  
- **Attach relevant logs or screenshots:** Include error messages, log files, or plots that illustrate the problem.  
- **Minimal reproducible example:** If possible, provide a small example that reproduces the issue.  

Following these guidelines makes it much easier for the developers to understand, reproduce, and fix your issue promptly.


--- 


## FAQ    

We are compiling the most common questions.


### No results in simulation outputs  
- Did the simulation file, or just the analyzer?
- For all models, or only for specific models?
- **Simulation failed**   
  - Check the log/error files.   
  - Possible causes:   
    - Simulation cancelled due to memory or time limit   
    - Input file errors prevented submission   
- **Raw simulation files exist, analyzer did not run correctly**    
  - Re-run the corresponding job submission file, or copy the command into the terminal.
  - Run analyzer interactively



---
  
