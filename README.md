# OSINT planform 
*This project is will WIP*
Using docker container to spin up isolated browser 

Instead of spinning up a entire virtual computer using VMware or Virtualbox, the goal of this project is too use a 

## Usage

In the scenario we have a enviroment file called .env.case001, which we usage to setup the docker container.

````bash
docker-compose --env-file .env.case001 -p case001 up -d
````


# How to setup SWAG

In the docker-compose.yml file, choose dns as the value next to VALIDATION

For cert provider its best to choose zerossl (because it allows you unlimited retries, unlike Letsencrypt)

For DNSPLUGIN, choose duckdns or whatever service you are using

Keep the rest as is, if you don't want to try any complexity

Now after starting the docker container using docker compose up (best not to include -d) and letting it show you some errors, bring it down using CTRL+C and docker compose down

Now go to the config/dnsconf/duckdns.ini and enter your Duckdns token

Restart the container using docker compose up -d and check if you have access to SWAG

For reverse proxy

Bring down the container

Copy config/nginx/proxy-conf/<service_name>.conf.sample to config/nginx/proxy-conf/<service_name>.conf

In the config/nginx/proxy-conf/<service_name>.conf file, change the server address in the $upstream_app to the local IP address

DO NOT forget to change the server_name too in the .conf file

Edit /etc/hosts on the local DNS server or in the Pi Hole DNS settings

Bring up the container using docker compose up -d

That is it. Hope it helps. And thank you to everyone who has helped me.