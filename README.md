# The ZA Project

ZA is a tool used to synchronize local files to the server.
It is designed for situations that have to synchronize files very frequently,
like debugging a server-side program.
The tool has the following features:
- Store server associated information, such as host name, user name, password
and project directory path.
- Automatically recognize the modified files and only upload the new version
instead of upload the whole folder.

## Examples

### Initialize a ZA controlled directory
```bash
# If the directory that you want to synchronize is placed at /home/user/proj
cd /home/user/proj
# Initialize
za.py -n
```
Then, you are asked for a "hostname", a "username", the corresponding
"password" and the target project directory path on the server.

### Synchronize the directory
```bash
# Go to the project directory
cd /home/user/proj
# Synchronize
za.py
```

### Ignore unnecessary directories and files
Edit the configure file:
```bash
vi /home/user/proj/.za/conf.json
``` 
Add an "ignore_list" attribute:
```json
{
    "username": "user",
    "project_dir": "proj",
    "hostname": "hostname",
    "password": "password",
    "ignore_list": [
        "__pycache__",
        "data",
    ]
}
```
Note that hidden directories (whose name starts with ".") are ignored by
default.

## About the Tool's Name

Someone maybe interested in the question: "Why is it called za ?"
Well, "za" is not short for any English phrase that have actual meanings.
However, the truth may be sound a little disappointed,
since I just choose two letters which lays closely form each other on the
 keyboard.
 Or it may be named after
a wonderful kawaii girl's name... Erm... Who cares~
