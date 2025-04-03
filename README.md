# ntt-cpp-library-manager

The python project for managing the NTT C++ library. At the starting moment, each project should has the configure
file `ntt-lib.json` which is from the root directory of the project.

All the projects (both project and dependencies) should be cloned only once into the `vendor` directory.

# How to install

## Install the executable file directly

Download the executable file from the release page and run it from here

## Build from source

# How to use
The example of the project structure is as follows:

```
.
├── ntt-lib.json
├── src
├── include
├── tests
├── CMakeLists.txt
└── vendor
```

The example content of the `ntt-lib.json` is as follows:

```json
{
    "version": "1.0.0",
    "dependencies": [
        {
            "folder": "project1", // the folder name of the project in the `vendor` directory
            "github": "https://github.com/project1", // the github repository url
            "commit": "1234567890" // optional, default is the latest commit
        },
        {
            "folder": "project2",
            "github": "https://github.com/project2",
            "commit": "1234567890"
        }
    ]
}
```

Run the executable file from the root directory of the project. 
```bash
pwd # the root directory of the project

manager.exe # the executable file at the root directory of the project
```

If the `project 1` and `project 2` have the same vendor (like `googletest`) then only one `googletest` folder will be cloned into the `vendor` directory so that the `vendor` folder will be like this:

```
.
├── googletest
├── project1
├── project1
└── CMakeLists.txt
```

# Acknowledgement
If you like this project, you can give me a star, or you can also send the feedback to me via the email `threezinedine@gmail.com`.