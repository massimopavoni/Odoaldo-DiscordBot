# **Odoaldo-DiscordBot**
[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/massimopavoni/Odoaldo-DiscordBot?include_prereleases)](https://github.com/massimopavoni/Odoaldo-DiscordBot/releases)
[![GitHub License](https://img.shields.io/github/license/massimopavoni/Odoaldo-DiscordBot)](https://github.com/massimopavoni/Odoaldo-DiscordBot/blob/master/LICENSE)

[![Discord](https://img.shields.io/discord/926217143194886234?label=Join%20Not%20Declared%20Developers)](https://discord.gg/ZA76nJ3RsU)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/T6T8BD7A1)

> _"Odoaldo, un personaggio particolarmente benvoluto, va in refettorio a mangiare un panino con la mortadella."_
> 
> **21 Aprile 2018 - _Giacomo_**

### **Dependencies**
- [discord.py](https://pypi.org/project/discord.py/) ([LICENSE](https://github.com/Rapptz/discord.py/blob/master/LICENSE))
- [pymongo](https://pypi.org/project/pymongo/) ([LICENSE](https://github.com/mongodb/mongo-python-driver/blob/master/LICENSE))
- [arithmetic-dice-roller](https://pypi.org/project/arithmetic-dice-roller/) ([LICENSE](https://github.com/massimopavoni/arithmetic-dice-roller/blob/main/LICENSE))

## **Disclaimer**
I am <ins>**not**</ins> responsible for how you use this code, nor am I accountable for whatever important purpose you need Odoaldo to serve: the Discord bot here developed has currently not been tested against most potential security issues, and should not be blindly trusted to be a proper shield between Discord and the machine the code is hosted on.

That being said, do remember to contact me beforehand in case you decide to use Odoaldo-DiscordBot for your own server.

## **Important**
The bot is designed to be run on a single server, and for this reason does <ins>**not**</ins> contemplate situations in which he's forced to deal with commands coming from two different servers, especially for voice channel features and dynamic database content.
I have yet to implement a block for the bot joining other servers, and that is still <ins>not a priority</ins> anyway.

## **Setup**
Follow the instructions to build and deploy your Odoaldo bot.

The Discord bot runs inside a python custom container, connected to a Mongo instance.<br>
It is possible to change the connection to the database, and just use the python container with another instance, but the setup I'm proposing here uses `docker compose` and some environment setup scripts to achieve a very simple architecture.

This guide assumes you know how to create a Discord application on the [Developer Portal](https://discord.com/developers/applications) and where to find the bot token.<br>
I'm also assuming you would wanna deploy Odoaldo on a machine other than your own, and for this reason we use [DockerHub](https://hub.docker.com/) as a means to deliver the custom python image.<br>
Furthermore, we push the image always with the same tag, as to allow the use of a private repository with other projects' tags.

Everything following works on Linux based distros (but you can imagine from the steps and the contents of the scripts how you would setup a different host machine), and **only** for `Odoaldo-DiscordBot >= 2.0.0`

### **Step 1:** Building Odoaldo custom docker image
Download the source code archive from the [releases](https://github.com/massimopavoni/Odoaldo-DiscordBot/releases) or clone the repository with:
```
git clone https://github.com/massimopavoni/Odoaldo-DiscordBot.git
```
Then place yourself inside the main directory and edit the `docker-build-env.sh` script with the necessary variables:
```
cd Odoaldo-DiscordBot

vim scripts/docker-build-env.sh
```
Here's the environment configuration, as per how it's used by the `Dockerfile`.<br>
Note that the mongo host should be set to `odoaldo-mongo` only if you're using the proposed setup with `docker compose`, since that's gonna use the specified network and container names.
```bash
#!/bin/bash

export DOCKERHUB_USER=
export DOCKERHUB_REPOSITORY=
export DISCORD_TOKEN=
export MONGO_USER=
export MONGO_PASSWORD=
export MONGO_HOST=odoaldo-mongo
export MONGO_PORT=
```
Remember to create the DockerHub reporitory you specified and login if it's a private one, then simply run the build and push script:
```
. scripts/docker-clean+build+push.sh
```
**Alternatively** to the previous steps, run the build script inside the directory you wanna build Odoaldo-DiscordBot in:
```
. <(curl https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/build.sh)
```

### **Step 2:** Deploying Odoaldo on host machine
First, create the structure for the `odoaldo` command:
```
mkdir -p ~/.local/bin/.odoaldo && cd $_
```
Then, copy the necessary docker files inside `.odoaldo` and the `odoaldo` command script in `bin`:
```
curl -OOO https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/{docker-clean+pull.sh,docker-deploy-env.sh,odoaldo_docker-compose.yml}

cd .. && curl -O https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/odoaldo
```
Remember to make the `odoaldo` script runnable with:
```
chmod +x odoaldo
```
Once again, edit the `docker-deploy-env.sh` script with the necessary variables:
```
vim .odoaldo/docker-deploy-env.sh
```
Here's the environment configuration:
```bash
#!/bin/bash

export DOCKERHUB_USER=
export DOCKERHUB_REPOSITORY=
export MONGO_USER=
export MONGO_PASSWORD=
export MONGO_PORT=
```
Remember to login to DockerHub if the repository is private, then simply go back to the home and run `odoaldo`:
```
cd ~
odoaldo
```
**Alternatively** to the previous steps, run the deploy script:
```
. <(curl https://raw.githubusercontent.com/massimopavoni/Odoaldo-DiscordBot/master/scripts/deploy.sh)
```
Make sure to have `$HOME/.local/bin` added to your `PATH` variable, to be able to run `odoaldo`. If that is not the case, add the export line to the `.bashrc` of the user running docker on the host machine:
```
echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
```

### **Step 3:** Managing Odoaldo with docker
The `odoaldo` command will always delete the containers and restart the whole pull and docker compose workflow, meaning you should only use the command when that's needed (i.e. when one of the two images involved is updated).

You should instead manage the Discord bot using the usual docker commands and utilities, as well as checking the logs with `docker attach odoaldo` or `docker logs odoaldo`, if there are some problems, or every once in a while anyway.

Pay close attention to the management commands available to admins (see `.help`), to understand how they work, and when they should be used, instead of operating on the dockers instances.
