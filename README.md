# stacher

> Very first version of Stacher is release :tada:

statistic fetcher for travian kingdom statistic on your gameworld.
it fetch the statistic every 10 minute mark.


[![Python 3.6](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/release/python-367/)

### how it work
the script will try to collecting statistic ranking on every avatar you have. to exclude some gameworld, use `exclude` parameter.

### installation
1. git clone [this repo](https://github.com/didadadida93/stacher.git)
2. change directory to stacher then create a python file

```python
from stacher import Stacher

email = 'dummy@email.com'
password = 'dummypassword'

Stacher(email, password, exclude=['com1', 'com2'])
```

3. execute the script: `python3 filename.py`

### attention
- it was intended that Stacher only kept one account.
- it was intended that Stacher fetching statistic sequentially (fetching population ranking first then fetching attack point ranking lastly fetching deffend point ranking) to avoid sending requests at same time.
- there is unidentification bug out there, if you don't mind please make an issue

#### thank you for
- [@scriptworld](https://github.com/scriptworld-git) for inspiring me and everything you have taught
- [@lijok](https://github.com/lijok) for sharing the script

---
_we love lowercase_
