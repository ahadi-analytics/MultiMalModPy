
# Versioning and Release Management  

MultiMalModPy uses semantic versioning to track and manage stable releases and development progress.   
Each version represents a distinct state of the codebase, including core framework updates, new models, and enhancements.  

---
 
## Versioning 

MultiMalModPy follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) for public releases with a  `-devN` suffix used for development and pre-release versions.

There are two version types used in MultiMalModPy: 

### Stable (Public) Releases

Stable versions are intended for public use and tagged as:  `MAJOR.MINOR.PATCH`  
 
**Examples:**
- `1.0.0`
- `1.12.0`
 
These versions are:
- Fully tested and documented
- Considered production-ready
- Uploaded to the [GitHub Releases](https://github.com/ahadi-analytics/MultiMalModPy/releases) page  


### Development Releases 

Development versions use the same format as stable releases but include a `-devN` suffix: `MAJOR.MINOR.PATCH-devN`  

**Examples:**
- `0.12.0-dev1` (first development snapshot for the future `0.12.0` release)  
- `1.13.0-dev2` (second iteration preparing for `1.13.0`)

These versions:
- Represent in-progress work
- May be unstable or incomplete
- Are suitable for testing or internal use

---

## Releasing a new version  

A release of MultiMalModPy is considered a version which has new models implemented in a state we consider as stable and tested.  

A stable release should include:
- Completed and tested features (e.g., new models, improved workflows)
- Documentation updates reflecting the changes
- Passing unit and integration tests

###  Release workflow:

Releases are made manually and  not yet compiled and tested automatically by the Continuous Integration system and uploaded to the Github Releases page.

1. **Tag the version in Git:**  
   ```bash  
   git tag v1.12.0  
   git push origin v1.12.0  

2. **Update version references:**  
   - In `docs/about/changelog.md`  
   - Push documentation `mkdocs gh-deploy`   

3. Create a GitHub Release:  
 - Add a summary of changes  
 - Attach release assets  


## Tests   
Testing is under active development and will be organized into:
- Unit Tests: For low-level logic (e.g., parameter calculation, configuration validation)  
- Integration Tests: For full simulation workflows, platform integration, and CLI usage  


##  Future Plans   

- Automate version tagging, release creation, changelog creation, and tests, with GitHub Actions
 
 