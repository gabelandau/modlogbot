import constants, praw, os, time, datetime, sys, logging, math, puni, slack
from puni import Note
from dhooks import Webhook, Embed
from loguru import logger
from sys import stdout

CLIENT_ID         = constants.CLIENT_ID
CLIENT_SECRET     = constants.CLIENT_SECRET
CLIENT_USERNAME   = constants.CLIENT_USERNAME
CLIENT_PASSWORD   = constants.CLIENT_PASSWORD
USER_AGENT        = constants.USER_AGENT
SUBREDDIT         = constants.SUBREDDIT
FLAIRCOMMENTS     = constants.FLAIRCOMMENTS
DISCORDHOOK       = constants.DISCORD_HOOK
SLACK_TOKEN       = constants.SLACK_TOKEN
CHECKAUTOMOD      = constants.CHECKAUTOMOD

reddit = None
subreddit = None
pushshift = None
usernotes = None
slack_client = None

###########################################
# Main function
###########################################
def main():
  if not initialize():
    sys.exit()

  startup()
  monitor_mod_log()


###########################################
# Monitor moderation log
###########################################
def monitor_mod_log():
  logger.info('Starting mod log scan...')
      
  # Start scanning mod log
  try:
    for action in praw.models.util.stream_generator(reddit.subreddit(SUBREDDIT).mod.log, skip_existing=True, attribute_name="id"):
      if action.action == 'editflair' and not action._mod == CLIENT_USERNAME:
        handle_mod_action(action)
      elif CHECKAUTOMOD and action.action == 'wikirevise' and action.details == 'Updated AutoModerator configuration':
        handle_automod_action(action)
  except Exception as e:
    logger.warning(e)
    pass


# Handle moderation action
def handle_mod_action(action):
  action_prefix = action.target_fullname.split("_", 1)[0]
  action_id = action.target_fullname.split("_", 1)[1]

  if action_prefix == 't3':
    mod = action._mod
    author = action.target_author
    parent = reddit.submission(id=action_id)
    flair = parent.link_flair_template_id

    for item in FLAIRCOMMENTS:
      if item['flair_id'] == flair:
        parent.mod.flair(text=item['flair_text'])
        comment = parent.reply(item['template'].substitute(username=author, submission=parent.title))
        comment.mod.distinguish(how='yes', sticky=True)
        parent.mod.remove()
        comment.mod.approve()

        if 'usernote' in item:
          note = puni.Note(author, item['usernote'], mod=mod, link=parent.url, warning='spamwatch')
          usernotes.add_note(note)
          logger.info('Usernote added.')

        discord_removal_msg(parent, mod)

        logger.info('{} removed a post with flair: {}'.format(mod, item['flair_text']))


# Handle automoderator update
def handle_automod_action(action):
  mod = action._mod

  slack_client.chat_postMessage(
    channel="GKW11PN72",
    link_names=True,
    text="<!channel>, /u/%s updated AutoMod configuration." % (mod)
  )
  
  logger.info('{} updated AutoMod configuration.'.format(mod))


###########################################
# Send Discord removal message
###########################################
def discord_removal_msg(parent, mod):
  embed = Embed(title='Moderator Removed Submission')
  embed.add_field(name='Submission', value='[%s](http://reddit.com%s)' % (parent.title, parent.permalink), inline=False)
  embed.add_field(name='Author', value='[%s](http://reddit.com/u/%s)' % (parent.author.name, parent.author.name), inline=False)
  embed.add_field(name='Flair Used', value=parent.link_flair_text, inline=False)
  embed.add_field(name='Details', value="%d point(s), %d comments" % (parent.score, len(parent.comments)))
  embed.add_field(name='Submitted On', value=time.strftime('%m/%d/%Y %H:%M GMT', time.gmtime(parent.created_utc)), inline=False)
  embed.add_field(name='Action Taken By', value='[%s](http://reddit.com/u/%s)' % (mod, mod), inline=False)

  Webhook(DISCORDHOOK).send(embed=embed)


###########################################
# Initialize bot & variables
###########################################
def initialize():
  global reddit
  global pushshift
  global subreddit
  global usernotes
  global slack_client

  try:
    logging.basicConfig(level=logging.INFO)
  except Exception as e:
    logger.error('Error creating log directory or logging.')
    print(e)
    return False

  try:
    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT, username=CLIENT_USERNAME, password=CLIENT_PASSWORD)
  except (Exception) as e:
    logger.error('Error initializing reddit/subreddit instances.')
    return False

  if CHECKAUTOMOD:
    try:
      slack_client = slack.WebClient(token=SLACK_TOKEN)
    except (Exception) as e:
      print(e)
      logger.error('Error initializing slack instances.')
      return False

  try:
    usernotes = puni.UserNotes(reddit, reddit.subreddit(SUBREDDIT))
  except (Exception) as e:
    print(e)
    logger.error('Error initializing usernotes instances.')
    return False

  return True


###########################################
# Print main menu
###########################################
def startup():
  logger.add(stdout, format="{time:HH:mm:ss} | {message}")
  logger.info('Starting {}'.format(USER_AGENT))


###########################################
# Execute main method
###########################################
if __name__ == "__main__":
  main()