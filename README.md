# Heath

This Grasshopper plugin provides a UI for life cycle building performance assessment in the Rhino environment. The plugin is not yet [available on Food4Rhino, but its sister app Brimstone is](https://www.food4rhino.com/en/app/brimstone?lang=en).

## Installation instructions
Dependencies:
- HumanUI
- Human
- eleFront
- Telepathy
- Heteroptera
- Wombat
- MetaHopper
 
1. Copy and paste the following file and folders to the Grasshopper User Object* folder:
- heath, (folder)
- brimstone_data, (folder)
- brimstone.py, (file)
2. Save the Rhino file before launching Heath.
3. Open Heath through Grasshopper. 
4. If you don't have all the plug-ins, just click download. Mathplotlib, numpy and other python packages will be installed automatically the first time the file is opened.

*The User Object folder can be accessed in Grasshopper through:
File -> Special Folders -> User Object Folder
or at: `C:\Users\[your name]\AppData\Roaming\Grasshopper\UserObjects`

## Features
* N/A

## Development
* Ongoing development happens in `dev` branch
* Releases are merged into `main` branch
* Versions [use semantic version](semver.org)

### Folders
* /dist - contains releases
* /doc - contains documentation
* /model - contains .gh and .3dm files
* /src - contains source code
* /test - contains testing files

### Releasing a new version
* Update heath_globals.version in src/heath.py
* Update current_gh_version input of "Heath - Fly!" component in .gh model

### Git usage (general)
* `git add .` to add all changes made
* `git commit -m"chore/fix/feat: short description of commit"` to document
    * Use `chore` for minor changes, `fix` for bug fix, `feat` for new feature

### Git usage (authorised users)

* Make sure Rhino/GH files are not open
* `git pull` to get updates from server (fix any merge issues)
* `git push` to push to server

### Git usage (unauthorised users)

* In GitHub, navigate to https://github.com/sawenchalmers/heath/
* Create a fork
    * In the top bar, click "Fork" and "+ Create a new fork"
* Clone the fork
* Make any changes locally
* When you are ready to merge with the main branch, create a pull request
    * In GitHub, navigate to your forked repository
    * Press "sync changes" to get any changes from the main repository
    * In GitHub, navigate to https://github.com/sawenchalmers/heath/
    * Click "New pull request"
    * Click "compare across fork" under the page title
    * Select the main fork as the "base repository"
    * Select your fork as the "head repository"
    * Click "Create pull request"
    * Give the pull request a title and comments as relevant
    * Click "Create pull request"
    * Done!

## Contact

Author: Toivo Säwén, sawen@chalmers.se

Contributors: Isac Mjörnell, misac@chalmers.se; Jieming Yan, jieming@chalmers.se; Lina Eriksson, linaerik@student.chalmers.se

## Changelog

### 0.6.0
* Major changes to UI and added features

### 0.5.0

### 0.4.0

* Back-end updates
* New logo celebration!

### 0.3.0

* Back-end updates

### 0.2.0

* Updates to UI and back-end

### 0.1.0

* Initial version
