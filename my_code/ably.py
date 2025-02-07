import asyncio
import time
from ably import AblyRealtime

async def main():

  # Connect to Ably with your API key
  ably = AblyRealtime('5jQJNw.LBPkOw:A9n44Rwi2zoh9ZyAOvzXPDg89VDGiudChEfFCGJXYNg')
  await ably.connection.once_async('connected')
  print('Connected to Ably')

  # Create a channel called 'get-started' and register a listener to subscribe to all messages with the name 'first'
  channel = ably.channels.get('get-started')
  def listener(message):
      print('Message received: ' + message.data)
  await channel.subscribe('first', listener)

  # Publish a message with the name 'first' and the contents 'Here is my first message!'
  time.sleep(1)
  await channel.publish('first', 'Here is my first message!')

  # Close the connection to Ably after a 5 second delay
  time.sleep(5)
  await ably.close()
  print('Closed the connection to Ably.')

asyncio.run(main())
