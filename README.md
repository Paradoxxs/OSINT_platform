# OSINT planform 

Using docker container to spin up isolated browser 

Instead of spinning up a entire virtual computer using VMware or Virtualbox, the goal of this project is too use a 

## Usage

In the scenario we have a enviroment file called .env.case001, which we usage to setup the docker container.

````bash
docker-compose --env-file .env.case001 -p case001 up -d
````
