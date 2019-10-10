import constants
import praw
import os
import time
import datetime
import sys
import logging
import math
import puni
import slack

from puni import Note
from dhooks import Webhook, Embed
from loguru import logger
from sys import stdout


"""
Static Classes

Settings, SlackClient, DiscordClient, and Reddit
"""
class Settings:
  check_auto_mod = None
  flairs = None


class SlackClient:
  token = None
  client = None

  @staticmethod
  def handle_automod_action(action):
    mod = action._mod

    SlackClient.client.chat_postMessage(
      channel="GKW11PN72",
      link_names=True,
      text="<!channel>, /u/%s updated AutoMod configuration." % (mod)
    )
    
    logger.info('{} updated AutoMod configuration.'.format(mod))


class DiscordClient:
  hook = None

  @staticmethod
  def discord_removal_msg(parent, mod):
    embed = Embed(title='Moderator Removed Submission')
    embed.add_field(name='Submission', value='[%s](http://reddit.com%s)' % (parent.title, parent.permalink), inline=False)
    embed.add_field(name='Author', value='[%s](http://reddit.com/u/%s)' % (parent.author.name, parent.author.name), inline=False)
    embed.add_field(name='Flair Used', value=parent.link_flair_text, inline=False)
    embed.add_field(name='Details', value="%d point(s), %d comments" % (parent.score, len(parent.comments)))
    embed.add_field(name='Submitted On', value=time.strftime('%m/%d/%Y %H:%M GMT', time.gmtime(parent.created_utc)), inline=False)
    embed.add_field(name='Action Taken By', value='[%s](http://reddit.com/u/%s)' % (mod, mod), inline=False)

    Webhook(DiscordClient.hook).send(embed=embed)


class RedditClient:
  credentials = None
  reddit = None
  subreddit = None
  usernotes = None

  @staticmethod
  def monitor_mod_log():
    logger.info('Starting mod log scan for /r/%s...' % (RedditClient.subreddit))
        
    try:
      for action in praw.models.util.stream_generator(RedditClient.reddit.subreddit(RedditClient.subreddit).mod.log, skip_existing=True, attribute_name="id"):
        if action.action == 'editflair' and not action._mod == RedditClient.credentials['username']:
          RedditClient.handle_mod_action(action)
        elif Settings.check_auto_mod and action.action == 'wikirevise' and action.details == 'Updated AutoModerator configuration':
          SlackClient.handle_automod_action(action)
    except Exception as e:
      logger.warning(e)
      pass

  @staticmethod
  def handle_mod_action(action):
    action_prefix = action.target_fullname.split("_", 1)[0]
    action_id = action.target_fullname.split("_", 1)[1]

    if action_prefix == 't3':
      try:
        mod = action._mod
        author = action.target_author
        parent = RedditClient.reddit.submission(id=action_id)
        flair = parent.link_flair_template_id

        for item in Settings.flairs:
          if item['flair_id'] == flair:
            parent.mod.flair(text=item['flair_text'])
            comment = parent.reply(item['template'].substitute(username=author, submission=parent.title))
            comment.mod.distinguish(how='yes', sticky=True)
            parent.mod.remove()
            comment.mod.approve()

            if 'usernote' in item:
              note = puni.Note(author, item['usernote'], mod=mod, link=parent.url, warning='spamwatch')
              RedditClient.usernotes.add_note(note)
              logger.info('Usernote added.')

            DiscordClient.discord_removal_msg(parent, mod)

            logger.info('{} removed a post with flair: {}'.format(mod, item['flair_text']))
      except Exception as e:
        pass


"""
Root Level Methods

Startup, Initialize, and __main__
"""
def initialize():
  try:
    RedditClient.credentials = {
      'client_id': constants.CLIENT_ID,
      'secret': constants.CLIENT_SECRET,
      'username': constants.CLIENT_USERNAME,
      'password': constants.CLIENT_PASSWORD,
      'agent': constants.USER_AGENT
    }

    RedditClient.subreddit = constants.SUBREDDIT

    Settings.flairs = constants.FLAIRCOMMENTS
    Settings.check_auto_mod = constants.CHECKAUTOMOD

    SlackClient.token = constants.SLACK_TOKEN
    DiscordClient.hook = constants.DISCORD_HOOK
  except Exception as e:
    print(e)
    logger.error('Error accessing configuration data.')
    return False

  try:
    logging.basicConfig(level=logging.INFO)
  except Exception as e:
    logger.error('Error creating log directory or logging.')
    print(e)
    return False

  try:
    RedditClient.reddit = praw.Reddit(
      client_id=RedditClient.credentials['client_id'],
      client_secret=RedditClient.credentials['secret'],
      user_agent=RedditClient.credentials['agent'],
      username=RedditClient.credentials['username'],
      password=RedditClient.credentials['password']
    )
  except (Exception) as e:
    print(RedditClient.credentials['client_id'])
    print(e)
    logger.error('Error initializing reddit/subreddit instances.')
    return False

  if Settings.check_auto_mod:
    try:
      SlackClient.client = slack.WebClient(token=SlackClient.token)
    except (Exception) as e:
      print(e)
      logger.error('Error initializing slack instances.')
      return False

  try:
    RedditClient.usernotes = puni.UserNotes(RedditClient.reddit, RedditClient.reddit.subreddit(RedditClient.subreddit))
  except (Exception) as e:
    print(e)
    logger.error('Error initializing usernotes instances.')
    return False

  return True


def startup():
  logger.add(stdout, format="{time:HH:mm:ss} | {message}")
  logger.info('Starting {}'.format(RedditClient.credentials['agent']))


def main():
  if not initialize():
    sys.exit()

  startup()
  RedditClient.monitor_mod_log()


if __name__ == "__main__":
  main()