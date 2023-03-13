#!/bin/bash

# Odoaldo-DiscordBot
# Copyright (C) 2021  Massimo Pavoni
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

git clone https://github.com/massimopavoni/Odoaldo-DiscordBot.git
cd Odoaldo-DiscordBot
vim scripts/docker-build-env.sh
printf "\nMake sure the variables you set are correct and run \". scripts/docker-clean+build+push.sh\"\n"
