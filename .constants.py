from string import Template

# =====================================
#
# Constants
#
# Duplicate this file as "constants.py" and change the variables
# below to match that of your Subreddit and Discord bot.
#
# Make sure to use Template syntax for the FLAIRCOMMENTS list.
# If you don't use the author's username ($username) or the
# submission title ($submission), you will have to edit the
# source code a bit to fix that. Check GitHub for details.
#
# =====================================

# Subreddit information
SUBREDDIT = 'flairbotdev'

# Reddit bot information, make sure everything here is filled out.
CLIENT_ID         = 'changeme'
CLIENT_SECRET     = 'changeme'
CLIENT_USERNAME   = 'changeme'
CLIENT_PASSWORD   = 'changeme'
USER_AGENT        = "FlairBot, a bot by /u/kellysama."
DISCORD_HOOK      = "changeme"

# Comments and flair IDs. Make sure you use the $username and $submission fields, or edit the source code.
FLAIRCOMMENTS = [
  {
    'flair_id': 'changeme',
    'flair_text': 'changeme',
    'template': Template('Hey there, $username! This post, $submission, was removed because it violated rule 1.')
  },
  {
    'flair_id': 'changeme',
    'flair_text': 'changeme',
    'template': Template('Hey there, $username! This post, $submission, was removed because it violated rule 2.')
  }
]