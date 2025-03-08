# MultiMalModPy Documentation


This folder contains the source code for generating the documentation, but most users can simply view it at https://ahadi-analytics.github.io/MultiMalModPy/.  

Documentation is created using [mkdocs](https://www.mkdocs.org/getting-started/) and the [read the docs theme](https://mkdocs.readthedocs.io/en/859/user-guide/custom-themes/).  


### To edit and view the documentation:

1. Set working directory and install dependencies
```
cd MultiMalModPy
pip install -r docs/requirements.txt
```

2. Start local serve
```
mkdocs serve
```

"_Open up http://127.0.0.1:8000/ in your browser, and you'll see the default home page being displayed:_"


3. Build docs

```
mkdocs build
```

4. Commit changes and push to GitHub

```
git add -A
git commit -m "Updated docs"
git push
```

If you do not have access rights to push directly, push to your forked repository and create a pull request on GitHub.com.


5. Deploy GitHub pages

This  only works when having access to the upstream repository.
In future versions, the gh-deply will be triggered automatically when docs are updated.

```
mkdocs gh-deploy
```

