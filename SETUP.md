# Pushing this to GitHub

Delete this file once you've pushed. It's instructions, not part of the project.

## One time, if you don't have git

    git --version

If missing: `winget install Git.Git`, then reopen the terminal.

    git config --global user.name "David Anthony"
    git config --global user.email "your@email.com"

## Create the repo

On github.com: New repository. Public. Do NOT tick "Add a README",
you already have one.

## Push

From inside this folder:

    git init
    git add .
    git commit -m "Pipeline path analysis"
    git branch -M main
    git remote add origin https://github.com/YOURNAME/REPONAME.git
    git push -u origin main

A browser opens on the last step to authenticate. Authorize it.

## After that

    git add .
    git commit -m "what changed"
    git push

## Before you push

Check nothing in this folder contains your HubSpot token (it starts with
`pat-na1-`). Once pushed, it's in the history even if you delete the file
later, and the fix is rotating the token.

`.gitignore` already covers .env files and hubspot.config.yml.
