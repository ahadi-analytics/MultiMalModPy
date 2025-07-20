
# Updating the MultiMalModPy Documentation

All documentation source files are located in the docs/ directory. 
Users can view the rendered version at:  
  [https://ahadi-analytics.github.io/MultiMalModPy/](https://ahadi-analytics.github.io/MultiMalModPy/)

The documentation is built using [MkDocs](https://www.mkdocs.org/getting-started/) with the [Read the Docs theme](https://mkdocs.readthedocs.io/en/859/user-guide/custom-themes/).
The site configuration is managed in [mkdocs.yml](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/mkdocs.yml).

---

## Editing and viewing the documentation locally (Windows)

### 1. Install Dependencies

Make sure you're in the project root directory, then install the required Python packages:


```
cd MultiMalModPy  
pip install -r docs/requirements.txt  
```

### 2. Shift to the docs branch to see latest edits

 If you're currently on another branch (e.g., main or dev) switch to docs and pull latest changes:  
```
git checkout docs
git pull
```


### 3. Serve the Documentation Locally

Start a local development server to preview latest and your additional changes:  

```
mkdocs serve
```

Open your browser and navigate to:  
🔗 http://127.0.0.1:8000/    

You should see the MultiMalModPy home page.  


### 4. Once done, build the static site

To generate the static site in the site/ directory:  

```
mkdocs build
```

### 5. Commit and push your changes   

If you've made changes to the documentation source, you have two main options:  


####  Push Directly (for quick updates)   
```
git add -A
git commit -m "Updated docs" 
git push
```

####  Preferred: Push to the docs Branch  
To keep documentation commits separate and reviewable via Pull Request:  

```
git checkout docs
git add -A
git commit -m "Updated docs"
git push origin docs
```



>  🔒 No Push Access to Upstream?: If you don’t have push access to the upstream repository, push to your fork and create a pull request on GitHub.


### 6. Merge with main and deploy GitHub pages

Only users with write access to the upstream repository can deploy documentation:  

```
mkdocs gh-deploy
```

 In future versions, this step will be automated as part of the CI/CD pipeline.   



