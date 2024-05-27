import hikari
import lightbulb
import json
import os


from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI()
bot = lightbulb.BotApp(
    token=os.getenv("BOT_TOKEN"),
    help_slash_command=True,
    intents=hikari.Intents.MESSAGE_CONTENT
)


@bot.command
@lightbulb.option(name='prompt', description='prompt', required=True)
@lightbulb.command(name='prompt', description='prompt')
@lightbulb.implements(lightbulb.SlashCommand)
async def ask(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": ctx.options.prompt}
        ]
    )

    await ctx.respond(completion.choices[0].message.content)


# @bot.command
# @lightbulb.command(name='compare', description='compare', aliases=['vergleichen'])
# @lightbulb.implements(lightbulb.SlashCommand)
# async def compare(ctx: lightbulb.SlashContext) -> None:
#     await ctx.respond("compare")


@bot.command
@lightbulb.option(name='name', description='Define the course name', type=hikari.OptionType.STRING)
@lightbulb.option(name='teacher', description='Define the teacher', type=hikari.OptionType.USER)
@lightbulb.command(name='create_course', description='Create a new course')
@lightbulb.implements(lightbulb.SlashCommand)
async def create_course(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

    data = {}

    os.makedirs(f'data/courses/{ctx.options.name}')
    os.makedirs(f'data/courses/{ctx.options.name}/files')

    await bot.rest.create_role(
        guild=ctx.guild_id,
        name=f'course_{ctx.options.name}'
    )

    json_string = json.dumps(data)

    file = open(f'data/courses/{ctx.options.name}/data.json', 'w')
    file.write(json_string)
    file.close()

    await ctx.respond("Success")


@bot.command
@lightbulb.option(name='course', description='course to add the file', type=hikari.OptionType.STRING, required=True)
@lightbulb.option(name='file', description='File to upload', type=hikari.OptionType.ATTACHMENT, required=True)
@lightbulb.command(name='upload', description='upload')
@lightbulb.implements(lightbulb.SlashCommand)
async def upload(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

    file = ctx.options.file
    await file.save(f'data/courses/{ctx.options.course}/files/{file.filename}')

    await ctx.respond("Success")


bot.run()
