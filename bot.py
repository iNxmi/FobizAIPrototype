import aspose.words
import hikari
import lightbulb
import json
import os
import time

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# delete temp files
for f in os.listdir(f'temp'):
    os.unlink(f'temp/{f}')

openai_client = OpenAI()
openai_assistant = openai_client.beta.assistants.create(
    name='Fobiz AI Prototype',
    instructions='You are a personal tutor. Read all files and answer questions only based on these files.',
    tools=[{"type": "file_search"}],
    model="gpt-4o",
)

bot = lightbulb.BotApp(
    token=os.getenv("BOT_TOKEN"),
    help_slash_command=True,
    intents=hikari.Intents.MESSAGE_CONTENT
)


@bot.command
@lightbulb.option(name='course', description='course', required=True)
@lightbulb.option(name='prompt', description='prompt', required=True)
@lightbulb.command(name='prompt', description='prompt')
@lightbulb.implements(lightbulb.SlashCommand)
async def prompt(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

    ms = round(time.time() * 1000)

    vector_store = openai_client.beta.vector_stores.create(name=str(ms))

    lst = os.listdir(f'data/courses/{ctx.options.course}/files')
    file_paths = []
    for l in lst:
        path = f'data/courses/{ctx.options.course}/files/{l}'
        if os.path.isfile(path):
            file_paths.append(path)

    file_streams = [open(path, "rb") for path in file_paths]
    file_batch = openai_client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    print(file_batch.status)
    print(file_batch.file_counts)

    assistant = openai_client.beta.assistants.update(
        assistant_id=openai_assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    thread = openai_client.beta.threads.create(
        messages=[
            {"role": "user", "content": ctx.options.prompt}
        ]
    )

    run = openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    messages = list(openai_client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = openai_client.files.retrieve(file_citation.file_id)
            citations.append(f"[{index}] {cited_file.filename}")

    print(message_content.value)
    print("\n".join(citations))

    path = f'temp/{ms}.txt'
    file = open(path, 'w')
    file.write(message_content.value)
    file.close()

    await ctx.respond(hikari.File(path))


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
